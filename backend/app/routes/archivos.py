import os
import io
import traceback
import requests
import joblib
from functools import lru_cache
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.utils.oci_storage import subir_archivo_oci, borrar_archivo_oci
from app.crud import guardar_documento_db
from app.database import get_db
from app.utils.limpieza_de_texto import extraer_texto_pdf_txt, chequear_duplicado, generar_resumen

router = APIRouter()

MODEL_URL = os.getenv("MODEL_URL")
VECTORIZER_URL = os.getenv("VECTORIZER_URL")

# Carga perezosa (Lazy Loading) con caché para no descargar los .pkl en cada petición
@lru_cache()
def cargar_artefactos_ml():
    if not MODEL_URL or not VECTORIZER_URL:
        raise ValueError("MODEL_URL o VECTORIZER_URL no están configuradas en las variables de entorno.")
    
    res_model = requests.get(MODEL_URL)
    res_model.raise_for_status()
    modelo = joblib.load(io.BytesIO(res_model.content))

    res_vec = requests.get(VECTORIZER_URL)
    res_vec.raise_for_status()
    vectorizer = joblib.load(io.BytesIO(res_vec.content))

    return modelo, vectorizer


@router.post("/contenido/archivo")
async def subir_y_procesar_archivo(
    request: Request,
    archivo: UploadFile = File(...),
    autor: str = Form("Desconocido"),
    tipo: str = Form("artículo"),
    db: Session = Depends(get_db)
):
    if not archivo.filename.endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Formato no soportado. Solo .pdf o .txt")

    url_archivo_oci = None
    subida_exitosa = False

    try:
        # 1. Subir archivo a OCI Object Storage
        url_archivo_oci = await subir_archivo_oci(archivo)

        # 2. Extracción de Texto Plano
        texto_crudo = await extraer_texto_pdf_txt(archivo)
        
        if not texto_crudo or len(texto_crudo.strip()) == 0:
            raise ValueError("NO_TEXT")

        # 3. Verificación de duplicados (Lógica existente)
        es_duplicado, titulo_original, similitud = (False, None, 0.0)

        if es_duplicado and similitud >= 0.80:
            subida_exitosa = True
            return {
                "mensaje": "El archivo ya existe en la base de conocimiento.",
                "documento_original": titulo_original,
                "similitud": float(similitud)
            }

        # 4. PREDICCIÓN REAL CON MODELO V2 Y VECTORIZADOR
        modelo, vectorizer = cargar_artefactos_ml()

        # Vectorizar texto y Predecir Categoría
        texto_vectorizado = vectorizer.transform([texto_crudo])
        categoria = str(modelo.predict(texto_vectorizado)[0])

        # Calcular Probabilidad Real
        probabilidades = modelo.predict_proba(texto_vectorizado)[0]
        probabilidad = float(round(max(probabilidades), 2))

        # Generar Resumen
        resumen_automatico = generar_resumen(texto_crudo)
        contenido_relacionado = ["IA", categoria, "OCI"]

        # 5. Guardar en Base de Datos Oracle con datos reales
        nuevo_id = guardar_documento_db(
            db=db,
            titulo=archivo.filename,
            texto=texto_crudo,
            autor=autor,
            categoria=categoria,
            probabilidad=probabilidad,
            resumen=resumen_automatico,
            tipo_archivo=archivo.filename.split('.')[-1],
            url_archivo=url_archivo_oci
        )

        subida_exitosa = True

        return {
            "id": nuevo_id,
            "categoria": categoria,
            "probabilidad": probabilidad,
            "contenido_relacionado": contenido_relacionado,
            "autor": autor,
            "tipo": tipo,
            "url_archivo": url_archivo_oci,
            "resumen": resumen_automatico
        }

    except ValueError as ve:
        if str(ve) == "NO_TEXT":
            raise HTTPException(status_code=400, detail="El documento no contiene texto digital legible (posible escaneo) o está vacío.")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        tb_str = traceback.format_exc()
        print(f"--- TRACEBACK COMPLETO ---\n{tb_str}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno al procesar el archivo: {str(e)}\n\nTRACEBACK:\n{tb_str}"
        )
    finally:
        if url_archivo_oci and not subida_exitosa:
            print(f"⚠️ Error detectado. Limpiando archivo huérfano de OCI: {url_archivo_oci}")
            await borrar_archivo_oci(url_archivo_oci)