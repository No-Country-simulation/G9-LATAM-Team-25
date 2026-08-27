"""
Configuración compartida de pytest para HoneyGuard.

IMPORTANTE: `app/database.py` construye una URL de conexión a Oracle
Autonomous Database a nivel de módulo, y `app/main.py` ejecuta
`Base.metadata.create_all(bind=engine)` en el momento del *import*.
Sin credenciales/red real hacia Oracle esto cuelga (reintentos largos
del DSN: retry_count=20, retry_delay=3) en vez de fallar rápido.

Para poder probar la lógica de la aplicación (rutas, dependencias,
serialización) sin esa conexión real, este conftest reemplaza el
`engine`/`SessionLocal` de Oracle por una base SQLite en memoria
*antes* de importar `app.main`, y sobreescribe la dependencia
`get_db` para que las rutas usen esa sesión de pruebas.

Esta sustitución es válida únicamente para probar la lógica de la
aplicación (columnas, tipos, flujo de commit/rollback a través del
ORM). No valida detalles específicos de Oracle (tipos NUMBER/CLOB,
dialecto SQL, latencia real, etc.), que quedan fuera del alcance de
lo verificable sin credenciales de producción.
"""

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

APP_ROOT = Path(__file__).resolve().parent.parent
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture()
def test_app():
    """Crea una instancia de la app FastAPI con Oracle sustituido por SQLite."""

    import app.database as dbmod

    # StaticPool es obligatorio aquí: sin él, cada conexión nueva que
    # abre SQLAlchemy (una por sesión) recibiría una base ":memory:"
    # distinta y vacía, y las tablas creadas por create_all() en la
    # primera conexión "desaparecerían" para el resto de la app.
    sqlite_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=sqlite_engine
    )

    dbmod.engine = sqlite_engine
    dbmod.SessionLocal = TestSessionLocal

    # Import diferido: solo aquí se ejecuta `Base.metadata.create_all`,
    # ya apuntando a SQLite.
    import importlib

    if "app.main" in sys.modules:
        importlib.reload(sys.modules["app.main"])
        main_module = sys.modules["app.main"]
    else:
        import app.main as main_module

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    main_module.app.dependency_overrides[dbmod.get_db] = override_get_db

    yield main_module.app

    main_module.app.dependency_overrides.clear()


@pytest.fixture()
def client(test_app):
    from fastapi.testclient import TestClient

    with TestClient(test_app) as c:
        yield c
