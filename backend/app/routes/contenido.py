from fastapi import APIRouter
from app.schemas import CargaContenidoRequest, CargaContenidoResponse
import uuid

router = APIRouter(
    prefix="/api/v1/contenido",
    tags=["Contenido"]
)

@router.post("/cargar", response_model=CargaContenidoResponse)
def cargar_contenido_simulado(request: CargaContenidoRequest):
    """
    Endpoint temporal (Mock) estructurado según la guía de Yeifry.
    """
    # Respuesta simulada respetando el contrato de la documentación oficial
    respuesta_mock = CargaContenidoResponse(
        id=str(uuid.uuid4())[:8],
        titulo=request.titulo if request.titulo else "Título Autogenerado",
        categoria="Backend", 
        probabilidad="0.89", 
        contenido_relacionado="Alta similitud detectada", 
        autor="Autor Desconocido",
        tipo="texto",
        url_archivo=request.url_archivo if request.url_archivo else "https://oci.oracle.com/mock-url"
    )
    
    return respuesta_mock