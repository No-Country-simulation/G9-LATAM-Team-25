# ... existing code ...
from fastapi import APIRouter, HTTPException
from app.schemas import CargaContenidoRequest
from app.utils.limpieza_de_texto import limpiar_texto

router = APIRouter()

@router.post("/api/v1/contenido/cargar")
async def cargar_contenido(datos: CargaContenidoRequest):
    # Importación local para evitar dependencias circulares con main.py
    from app.main import ml_resources
    
    # 1. Rescatar los modelos cargados en memoria
    modelo = ml_resources.get("modelo")
    vectorizador = ml_resources.get("vectorizador")
    
    if not modelo or not vectorizador:
        raise HTTPException(status_code=503, detail="Los modelos de IA no están cargados. Contacta a soporte.")

    # 2. Limpiar el texto crudo del usuario
    texto_limpio = limpiar_texto(datos.texto_crudo)
    
    # 3. Vectorizar (Convertir texto a matemática usando el vocabulario de Data Science)
    texto_vectorizado = vectorizador.transform([texto_limpio])
    
    # 4. Hacer la predicción
    categoria = modelo.predict(texto_vectorizado)[0]
    probabilidades = modelo.predict_proba(texto_vectorizado)[0]
    probabilidad_maxima = round(float(max(probabilidades)), 4) # Redondeado a 4 decimales
    
    # 5. Devolver la respuesta oficial
    return {
        "categoria": categoria,
        "probabilidad": probabilidad_maxima,
        "informacion_adicional": [], # Puedes extraer palabras clave aquí a futuro
        "titulo_recibido": datos.titulo_documento
    }
# ... existing code ...