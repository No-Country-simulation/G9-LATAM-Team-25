from fastapi import APIRouter
from app.schemas import CargaContenidoRequest

router = APIRouter()

@router.post("/api/v1/contenido/cargar")
async def cargar_contenido(datos: CargaContenidoRequest):
    # Ya no es un simulador básico, aquí recibimos datos validados
    return {
        "mensaje": "Datos recibidos correctamente",
        "titulo_recibido": datos.titulo_documento,
        "texto_longitud": len(datos.texto_crudo)
    }