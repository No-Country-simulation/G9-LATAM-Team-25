from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, Field


# ============================================================
# RECURSO DOCUMENTO
# ============================================================

class DocumentoCreate(BaseModel):
    texto: str = Field(min_length=1)
    titulo: Optional[str] = None
    tema: Optional[str] = None
    autor: Optional[str] = None
    formato_archivo: str = "texto"
    tipo_contenido: Optional[str] = None
    url_archivo: Optional[str] = None


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


class DocumentoListadoResponse(BaseModel):
    id: int
    titulo: Optional[str] = None
    autor: Optional[str] = None
    categoria: str
    probabilidad: float
    resumen: Optional[str] = None
    palabras_clave: Optional[List[str]] = None
    formato_archivo: str
    tipo_contenido: Optional[str] = None
    url_archivo: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class ListaDocumentosResponse(BaseModel):
    items: List[DocumentoListadoResponse]
    total: int
    offset: int
    limit: int


class ResultadoBusqueda(BaseModel):
    id: int
    titulo: Optional[str] = None
    autor: Optional[str] = None
    categoria: str
    probabilidad: float
    resumen: Optional[str] = None
    palabras_clave: Optional[List[str]] = None
    formato_archivo: str
    tipo_contenido: Optional[str] = None
    url_archivo: str
    fecha_creacion: datetime

    class Config:
        from_attributes = True


class RespuestaBusqueda(BaseModel):
    resultados: List[ResultadoBusqueda]
    total: int
    query: Optional[str] = None
    filtros: dict
    offset: int
    limit: int


# ============================================================
# CLASIFICACIÓN DIRECTA
# ============================================================

class ClasificarTextoRequest(BaseModel):
    texto: str = Field(min_length=1)
    top_n_palabras_clave: int = Field(default=8, ge=1, le=20)


class ClasificarTextoResponse(BaseModel):
    categoria: str
    probabilidad: float
    palabras_clave: List[str]
    requiere_revision: bool


# ============================================================
# RESPUESTAS DEL ENDPOINT DE CARGA
# ============================================================

class MetadatosResponse(BaseModel):
    id: int
    titulo: Optional[str] = None
    autor: Optional[str] = None
    formato_archivo: str
    tipo_contenido: Optional[str] = None
    url_archivo: str


class ClasificacionResponse(BaseModel):
    categoria: str
    probabilidad: float
    palabras_clave: List[str] = []
    resumen: Optional[str] = None
    requiere_revision: bool


class DocumentoRelacionado(BaseModel):
    id: int
    titulo: Optional[str] = None
    similitud: float


class ContenidoResponse(BaseModel):
    texto_extraido: str
    total_palabras: int


class RespuestaCargaExitosa(BaseModel):
    metadatos: MetadatosResponse
    clasificacion: ClasificacionResponse
    contenido_relacionado: List[DocumentoRelacionado] = []
    contenido: ContenidoResponse


class DocumentoOriginalDuplicado(BaseModel):
    id: int
    titulo: Optional[str] = None


class RespuestaDuplicado(BaseModel):
    mensaje: str
    documento_original: DocumentoOriginalDuplicado
    similitud: float


RespuestaCargaArchivo = Union[RespuestaCargaExitosa, RespuestaDuplicado]
