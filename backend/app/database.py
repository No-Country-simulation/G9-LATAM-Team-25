import os
import logging
import urllib.parse
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Carga el .env forzando el override de variables guardadas en memoria
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

logger = logging.getLogger(__name__)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Codificar caracteres especiales como el * para SQLAlchemy
encoded_password = urllib.parse.quote_plus(DB_PASSWORD) if DB_PASSWORD else ""

DSN = os.getenv(
    "ORACLE_DSN",
    "(description=(retry_count=20)(retry_delay=3)"
    "(address=(protocol=tcps)(port=1522)(host=adb.sa-bogota-1.oraclecloud.com))"
    "(connect_data=(service_name=gee6aa642c1f765_g9team25db_medium.adb.oraclecloud.com))"
    "(security=(ssl_server_dn_match=yes)))",
)

DATABASE_URL = f"oracle+oracledb://{DB_USER}:{encoded_password}@{DSN}"

# El eco de SQL (log de cada sentencia ejecutada, incluyendo parámetros)
# es útil en desarrollo pero puede filtrar contenido de documentos en
# los logs de producción. Se controla con la variable de entorno
# SQL_ECHO (opcional, no requerida). Por defecto queda apagado.
SQL_ECHO = os.getenv("SQL_ECHO", "false").strip().lower() == "true"

engine = create_engine(DATABASE_URL, echo=SQL_ECHO)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# ============================================================
# SESIÓN DE BASE DE DATOS (dependencia de FastAPI)
# ============================================================
# Esta es la función que antes se llamaba `guardar_documento_db`.
# Su nombre original era confuso: no guarda nada, solo entrega una
# sesión y la cierra al terminar. Se renombra a `get_db`, que es la
# convención estándar de FastAPI para este patrón, para no seguir
# confundiéndola con una función de persistencia real.

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================
# CREAR DOCUMENTO (persistencia real)
# ============================================================
# Antes no existía ninguna función que hiciera db.add()/db.commit().
# `Documento` se importa aquí adentro (import diferido) y no arriba
# del archivo, porque `app/models.py` importa `Base` desde este mismo
# archivo (`database.py`) -> importar `Documento` a nivel de módulo
# aquí crearía un import circular.

def crear_documento(
    db: Session,
    *,
    titulo: str | None,
    texto: str,
    autor: str | None,
    categoria: str,
    probabilidad: float,
    resumen: str | None,
    palabras_clave: list | None,
    contenido_relacionado: list | None,
    formato_archivo: str,
    tipo_contenido: str | None,
    url_archivo: str,
):
    """
    Crea y persiste un nuevo Documento en Oracle.

    Usa exactamente las columnas que ya existen en `app/models.py`
    (no se agregó ninguna columna nueva).

    Devuelve el objeto Documento ya guardado (con su `id` asignado
    por la base de datos). Si ocurre un error, hace rollback y
    vuelve a lanzar la excepción para que el endpoint decida cómo
    responder al cliente.
    """

    from app.models import Documento

    nuevo_documento = Documento(
        titulo=titulo,
        texto=texto,
        autor=autor,
        categoria=categoria,
        probabilidad=probabilidad,
        resumen=resumen,
        palabras_clave=palabras_clave,
        contenido_relacionado=contenido_relacionado,
        formato_archivo=formato_archivo,
        tipo_contenido=tipo_contenido,
        url_archivo=url_archivo,
    )

    try:
        db.add(nuevo_documento)
        db.commit()
        db.refresh(nuevo_documento)
        return nuevo_documento

    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error guardando documento en Oracle: {e}")
        raise


# ============================================================
# CONSULTAR DOCUMENTOS EXISTENTES (para duplicados/similitud)
# ============================================================
# Antes no existía ninguna consulta a la tabla Documento. Sin esto,
# chequear_duplicado() y calcular_similitud_recomendaciones() no
# tenían con qué comparar el documento nuevo.

def obtener_documentos_existentes(db: Session) -> list[dict]:
    """
    Devuelve los documentos ya guardados, en el formato que esperan
    `chequear_duplicado()` y `calcular_similitud_recomendaciones()`
    de app/ml_models/loader.py:

        [{"id": ..., "titulo": ..., "texto": ...}, ...]

    Si ocurre un error de Oracle, propaga la excepción para que el
    endpoint pueda abortar el flujo. Un fallo de base de datos no se
    interpreta como "no hay documentos", porque eso alteraría la
    detección real de duplicados.
    """

    from app.models import Documento

    try:
        filas = (
            db.query(Documento.id, Documento.titulo, Documento.texto)
            .all()
        )
        return [
            {"id": fila.id, "titulo": fila.titulo, "texto": fila.texto}
            for fila in filas
        ]

    except SQLAlchemyError as e:
        logger.error(f"Error consultando documentos existentes: {e}")
        raise

# ============================================================
# CONSULTAS DE DOCUMENTOS
# ============================================================

def obtener_documento_por_id(db: Session, documento_id: int):
    """Obtiene un documento completo por su ID desde Oracle."""
    from app.models import Documento

    return (
        db.query(Documento)
        .filter(Documento.id == documento_id)
        .first()
    )


def listar_documentos(
    db: Session,
    *,
    offset: int = 0,
    limit: int = 20,
    categoria: str | None = None,
    autor: str | None = None,
    tipo_contenido: str | None = None,
):
    """
    Lista documentos reales almacenados en Oracle con paginación y filtros.

    Devuelve una tupla: (documentos, total).
    """
    from app.models import Documento

    query = db.query(Documento)

    if categoria:
        query = query.filter(Documento.categoria == categoria)

    if autor:
        query = query.filter(Documento.autor == autor)

    if tipo_contenido:
        query = query.filter(Documento.tipo_contenido == tipo_contenido)

    total = query.count()

    documentos = (
        query
        .order_by(Documento.fecha_creacion.desc(), Documento.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return documentos, total


def buscar_documentos(
    db: Session,
    *,
    q: str | None = None,
    categoria: str | None = None,
    autor: str | None = None,
    tipo_contenido: str | None = None,
    offset: int = 0,
    limit: int = 20,
):
    """
    Busca documentos reales en Oracle.

    `q` se aplica sobre título, autor, categoría, tipo de contenido y
    texto almacenado. No utiliza mocks ni memoria local como fuente
    de resultados.
    """
    from sqlalchemy import or_, func
    from app.models import Documento

    query = db.query(Documento)

    if q and q.strip():
        termino = q.strip()
        patron = f"%{termino.lower()}%"

        query = query.filter(
            or_(
                func.lower(Documento.titulo).like(patron),
                func.lower(Documento.autor).like(patron),
                func.lower(Documento.categoria).like(patron),
                func.lower(Documento.tipo_contenido).like(patron),
                func.lower(Documento.texto).like(patron),
            )
        )

    if categoria:
        query = query.filter(Documento.categoria == categoria)

    if autor:
        query = query.filter(Documento.autor == autor)

    if tipo_contenido:
        query = query.filter(Documento.tipo_contenido == tipo_contenido)

    total = query.count()

    documentos = (
        query
        .order_by(Documento.fecha_creacion.desc(), Documento.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return documentos, total

