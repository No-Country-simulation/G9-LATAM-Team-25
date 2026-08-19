from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Estructura de Entrada (Lo que el usuario/cliente envía)
class DocumentoCreate(BaseModel):
    texto: str # Único campo estrictamente obligatorio para el análisis
    titulo: Optional[str] = None
    tema: Optional[str] = None
    autor: Optional[str] = None
    formato_archivo: str
    tipo_contenido: Optional[str] = None
    url_archivo: Optional[str] = None

# Estructura de Salida (Lo que responde la API tras procesar con la IA)
class DocumentoResponse(BaseModel):
    id: int
    titulo: Optional[str] = None
    tema: Optional[str] = None
    autor: Optional[str] = None
    categoria: str
    probabilidad: float
    texto: str
    resumen: Optional[str] = None
    palabras_clave: Optional[List[str]] = None
    contenido_relacionado: Optional[List[int]] = None
    formato_archivo: str
    tipo_contenido: Optional[str] = None
    url_archivo: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True