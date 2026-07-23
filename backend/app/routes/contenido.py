from fastapi import APIRouter
from app.schemas import ContenidoCreate, ContenidoResponse

router = APIRouter(prefix="/contenido", tags=["Contenido"])

@router.post("/", response_model=ContenidoResponse)
def crear_contenido_simulado(payload: ContenidoCreate):
    # Generamos una respuesta Mock (simulada) 
    return {
        "id": 101,
        "titulo": payload.titulo,
        "texto": payload.texto,
        "resumen": f"Resumen automático preliminar de: '{payload.titulo}'. El texto fue procesado de forma simulada.",
        "categoria": "Artículo Científico",
        "probabilidad": 0.94,
        "palabras_clave": ["ia", "fastapi", "oracle", "nlp"],
        "status": "success"
    }