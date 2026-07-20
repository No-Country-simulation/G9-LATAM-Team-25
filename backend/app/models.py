from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class ItemPrueba(Base):
    __tablename__ = "items_prueba"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)