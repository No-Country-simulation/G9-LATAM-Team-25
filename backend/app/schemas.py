from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, field_validator

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
class ContenidoCreate(BaseModel):
    titulo: str
    texto: str

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

# --- ESQUEMA CARGA CONTENIDO (Sincronizado) ---
class CargaContenidoRequest(BaseModel):
    titulo_documento: Optional[str] = None
    texto_crudo: str

    @field_validator('texto_crudo')
    def texto_no_vacio(cls, value):
        if not value or not value.strip():
            raise ValueError('El texto_crudo no puede estar vacio ni contener solo espacios en blanco.')
        return value