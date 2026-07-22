from pydantic import BaseModel
from typing import Optional

# JSON de Entrada (Request de cargue)
class CargaContenidoRequest(BaseModel):
    titulo: Optional[str] = ""
    texto: str  # El texto plano es obligatorio para el modelo
    url_archivo: Optional[str] = ""

# JSON de Salida (Response simulado)
class CargaContenidoResponse(BaseModel):
    id: str
    titulo: str
    categoria: str
    probabilidad: str
    contenido_relacionado: str
    autor: str
    tipo: str
    url_archivo: str