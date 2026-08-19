from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
# Importaciones simuladas de tus servicios internos (deberás crearlas/conectarlas):
from backend.app.utils.oci_storage import subir_archivo_oci, borrar_archivo_oci
from app.services.db_oracle import guardar_documento_db
from app.utils.data_science import extraer_texto_pdf_txt, chequear_duplicado, generar_resumen

router = APIRouter()

@router.post("/contenido/archivo")
async def subir_y_procesar_archivo(
    request: Request,
    archivo: UploadFile = File(...),
    autor: str = Form("Desconocido"),
    tipo: str = Form("artículo")
):
    # Validar formato
    if not archivo.filename.endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Formato no soportado. Solo .pdf o .txt")

    # 1. Subir archivo a OCI Object Storage
    url_archivo_oci = await subir_archivo_oci(archivo)

    try:
        # 2. Extracción de Texto Plano
        texto_crudo = await extraer_texto_pdf_txt(archivo)
        
        if not texto_crudo or len(texto_crudo.strip()) == 0:
            # Archivo ilegible (imagen escaneada o vacío)
            raise ValueError("NO_TEXT")

        # 3. Validación de Duplicados (Similitud Coseno)
        # Asumimos que la función retorna (es_duplicado, titulo_original, porcentaje)
        es_duplicado, titulo_original, similitud = chequear_duplicado(texto_crudo, request.app.state.vectorizador)

        if es_duplicado and similitud >= 0.80:
            # Borrar archivo huérfano de OCI
            await borrar_archivo_oci(url_archivo_oci)
            return {
                "mensaje": "El archivo ya existe en la base de conocimiento.",
                "documento_original": titulo_original,
                "similitud": float(similitud)
            }

        # 4. Procesamiento de IA (Clasificación, Keywords, Resumen)
        modelo = request.app.state.modelo
        vectorizador = request.app.state.vectorizador
        
        # Limpieza y Vectorización
        texto_vectorizado = vectorizador.transform([texto_crudo])
        categoria = str(modelo.predict(texto_vectorizado)[0])
        probabilidad = float(max(modelo.predict_proba(texto_vectorizado)[0]))
        
        resumen_automatico = generar_resumen(texto_crudo)
        
        # 5. Guardar en Base de Datos (Oracle Autonomous DB)
        nuevo_id = guardar_documento_db(
            titulo=archivo.filename,
            texto=texto_crudo,
            autor=autor,
            categoria=categoria,
            probabilidad=probabilidad,
            resumen=resumen_automatico,
            tipo_archivo=archivo.filename.split('.')[-1],
            url_archivo=url_archivo_oci
        )

        # 6. Retorno de JSON Estructurado
        return {
            "id": nuevo_id,
            "categoria": categoria,
            "probabilidad": probabilidad,
            "contenido_relacionado": [], # Vacio inicialmente, calculado dinámicamente en consultas
            "autor": autor,
            "tipo": tipo,
            "url_archivo": url_archivo_oci,
            "resumen": resumen_automatico
        }

    except ValueError as ve:
        # Manejo de error de extracción (Archivo escaneado o sin texto)
        await borrar_archivo_oci(url_archivo_oci) # Limpiar OCI antes de fallar
        if str(ve) == "NO_TEXT":
            raise HTTPException(status_code=400, detail="El documento no contiene texto digital legible (posible escaneo) o está vacío.")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        # Error general del servidor: Limpiamos OCI por seguridad
        await borrar_archivo_oci(url_archivo_oci)
        raise HTTPException(status_code=500, detail=f"Error interno al procesar el archivo: {str(e)}")