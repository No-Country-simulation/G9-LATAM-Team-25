from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# --- ESQUEMAS PARA ÍTEMS DE PRUEBA ---
class ItemCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class ItemResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    fecha_creacion: datetime

    class Config:
        from_attributes = True


# --- (POST /contenido) ---

# Estructura que envía el cliente (Checklist Trello)
class ContenidoCreate(BaseModel):
    titulo: str
    texto: str

# Respuesta simulada 
class ContenidoResponse(BaseModel):
    id: int
    titulo: str
    texto: str
    resumen: str
    categoria: str
    probabilidad: float
    palabras_clave: List[str]
    status: str

    class Config:
        from_attributes = True