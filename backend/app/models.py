import json
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    Sequence,
    String,
    Text,
    TypeDecorator,
)

from app.database import Base


# Secuencia utilizada por Oracle para generar automáticamente el ID.
documentos_id_seq = Sequence(
    "documentos_id_seq",
    metadata=Base.metadata,
    start=1,
    increment=1,
)


class OracleJSON(TypeDecorator):
    """
    Convierte listas o diccionarios de Python a texto para Oracle
    y los convierte nuevamente al consultar la base de datos.
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value, ensure_ascii=False)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)

        return value


class Documento(Base):
    __tablename__ = "documentos"

    id = Column(
        Integer,
        documentos_id_seq,
        primary_key=True,
    )

    titulo = Column(String(255), nullable=True)
    tema = Column(String(100), nullable=True)
    autor = Column(String(150), nullable=True)

    # Campos calculados por inteligencia artificial
    categoria = Column(String(100), nullable=False)
    probabilidad = Column(Float, nullable=False)

    # Contenido y resumen del documento
    texto = Column(Text, nullable=False)
    resumen = Column(Text, nullable=True)

    # Listas almacenadas como JSON dentro de columnas de texto
    palabras_clave = Column(OracleJSON, nullable=True)
    contenido_relacionado = Column(OracleJSON, nullable=True)

    # Metadatos del archivo
    formato_archivo = Column(String(10), nullable=False)
    tipo_contenido = Column(String(50), nullable=True)
    url_archivo = Column(String(500), nullable=False)

    fecha_creacion = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )