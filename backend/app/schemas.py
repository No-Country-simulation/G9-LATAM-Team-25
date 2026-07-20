from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Estructura para RECIBIR datos desde el cliente 
class ItemCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

# Estructura para RESPONDER al cliente (incluye el ID generado por la BD)
class ItemResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True