from fastapi import APIRouter, HTTPException, Request
from app.schemas import CargaContenidoRequest, CargaContenidoResponse
from app.utils.limpieza_de_texto import limpiar_texto # Tu función de NLP

router = APIRouter()

@router.post("/contenido", response_model=CargaContenidoResponse)
async def procesar_texto_directo(request: Request, payload: CargaContenidoRequest):
    try:
        # 1. Obtener modelos cargados en el lifespan
        modelo = request.app.state.modelo
        vectorizador = request.app.state.vectorizador

        # 2. Limpiar y Vectorizar el texto
        texto_limpio = limpiar_texto(payload.texto_crudo)
        texto_vectorizado = vectorizador.transform([texto_limpio])

        # 3. Predicción real
        prediccion = modelo.predict(texto_vectorizado)[0]
        probabilidades = modelo.predict_proba(texto_vectorizado)[0]
        confianza = max(probabilidades)

        # 4. Extracción de Palabras Clave (Top 3)
        nombres_features = vectorizador.get_feature_names_out()
        indices_top = texto_vectorizado.toarray()[0].argsort()[-3:][::-1]
        palabras_clave = [nombres_features[i] for i in indices_top]

        # 5. Mapeo a tipos nativos de Python para evitar errores de Pydantic
        categoria_str = str(prediccion)
        probabilidad_float = float(confianza)

        return {
            "categoria": categoria_str,
            "probabilidad": probabilidad_float,
            "informacion_adicional": palabras_clave
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar el modelo: {str(e)}")