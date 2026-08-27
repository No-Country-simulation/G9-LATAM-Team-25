"""
Pruebas de app/database.py: crear_documento() y
obtener_documentos_existentes().

No hay credenciales reales de Oracle disponibles en este entorno, así
que estas pruebas usan SQLite en memoria como sustituto para validar
la LÓGICA (add/commit/refresh, rollback en error, consulta de
existentes). No validan comportamiento específico del dialecto Oracle.
"""

import warnings

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

warnings.filterwarnings("ignore")


@pytest.fixture()
def db_session():
    import app.database as dbmod
    import app.models  # noqa: F401  (registra Documento en Base.metadata)

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    dbmod.Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    session = SessionLocal()
    yield session
    session.close()


def _kwargs_documento(**overrides):
    base = dict(
        titulo="test.pdf",
        texto="contenido de prueba",
        autor="autor",
        categoria="DevOps",
        probabilidad=0.9,
        resumen="resumen",
        palabras_clave=["a", "b"],
        contenido_relacionado=[],
        formato_archivo="pdf",
        tipo_contenido="articulo",
        url_archivo="https://x/y",
    )
    base.update(overrides)
    return base


def test_crear_documento_asigna_id_y_persiste(db_session):
    from app.database import crear_documento

    doc = crear_documento(db_session, **_kwargs_documento())

    assert doc.id is not None
    assert doc.titulo == "test.pdf"
    assert doc.categoria == "DevOps"


def test_crear_documento_rollback_en_error(db_session):
    from app.database import crear_documento
    from sqlalchemy.exc import SQLAlchemyError

    # `categoria` es NOT NULL en el modelo -> debe fallar y hacer rollback.
    with pytest.raises(SQLAlchemyError):
        crear_documento(db_session, **_kwargs_documento(categoria=None))

    # La sesión debe seguir siendo usable después del rollback.
    doc_ok = crear_documento(db_session, **_kwargs_documento(url_archivo="https://otra"))
    assert doc_ok.id is not None


def test_obtener_documentos_existentes_lista_vacia(db_session):
    from app.database import obtener_documentos_existentes

    assert obtener_documentos_existentes(db_session) == []


def test_obtener_documentos_existentes_devuelve_formato_esperado(db_session):
    from app.database import crear_documento, obtener_documentos_existentes

    crear_documento(db_session, **_kwargs_documento())
    existentes = obtener_documentos_existentes(db_session)

    assert len(existentes) == 1
    assert set(existentes[0].keys()) == {"id", "titulo", "texto"}
    assert existentes[0]["titulo"] == "test.pdf"
