from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from datetime import datetime
from app.database import Base

class ContenidoProcesado(Base):
    __tablename__ = "contenidos_procesados"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    titulo = Column(String(255), nullable=False)
    texto = Column(Text, nullable=False)
    autor = Column(String(100), nullable=True, default="Desconocido")
    categoria = Column(String(100), nullable=True)
    probabilidad = Column(Float, nullable=True)
    resumen = Column(Text, nullable=True)
    tipo_archivo = Column(String(10), nullable=False)
    url_archivo = Column("URL_ARCHIVO", String(512), nullable=False, unique=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)