from sqlalchemy import Column, Integer, String, Float, Text, JSON, DateTime
from datetime import datetime
from app.database import Base

class Documento(Base):
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    titulo = Column(String(255), nullable=True)
    tema = Column(String(100), nullable=True)
    autor = Column(String(150), nullable=True)
    
    # Campos calculados por la Inteligencia Artificial
    categoria = Column(String(100), nullable=False)
    probabilidad = Column(Float, nullable=False) 
    
    # Tipo Text para soportar el límite estricto de hasta 50,000 palabras
    texto = Column(Text, nullable=False) 
    resumen = Column(Text, nullable=True) # Guardado para evitar recalcularlo
    
    # Estructuras JSON
    palabras_clave = Column(JSON, nullable=True)
    contenido_relacionado = Column(JSON, nullable=True) # Lista de IDs de documentos similares
    
    # Separación arquitectónica para evitar colisión de conceptos
    formato_archivo = Column(String(10), nullable=False) # Ej: pdf, txt
    tipo_contenido = Column(String(50), nullable=True)   # Ej: artículo, módulo, apunte
    
    url_archivo = Column(String(500), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)