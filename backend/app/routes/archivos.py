import traceback # Importar para obtener el traceback completo
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Depends
from sqlalchemy.orm import Session

# Importaciones de servicios internos y base de datos
from app.utils.oci_storage import subir_archivo_oci, borrar_archivo_oci
from app.crud import guardar_documento_db
from app.database import get_db
from app.utils.limpieza_de_texto import extraer_texto_pdf_txt, chequear_duplicado, generar_resumen
from app.ml_models.loader import load_model # Importar load_model para el fallback

router = APIRouter()

@router.post("/contenido/archivo")
async def subir_y_procesar_archivo(
    request: Request,
    archivo: UploadFile = File(...),
    autor: str = Form("Desconocido"),
    tipo: str = Form("artículo"),
    db: Session = Depends(get_db)  # <-- Inyección de la sesión de base de datos
):
    # Validar formato
    if not archivo.filename.endswith(('.pdf', '.txt')):
        raise HTTPException(status_code=400, detail="Formato no soportado. Solo .pdf o .txt")

    # URL del archivo en OCI, se inicializa en None para el bloque finally
    url_archivo_oci = None
    try:
        # 1. Subir archivo a OCI Object Storage
        url_archivo_oci = await subir_archivo_oci(archivo)

        # 2. Extracción de Texto Plano
        texto_crudo = await extraer_texto_pdf_txt(archivo)
        
        if not texto_crudo or len(texto_crudo.strip()) == 0:
            # Archivo ilegible (imagen escaneada o vacío)
            raise ValueError("NO_TEXT")

        # ======================================================================
        # --- INICIO: BLOQUE DE DATOS SIMULADOS (MOCKS) PARA PRUEBAS ---
        # ======================================================================
        print("⚠️ Usando datos de ML simulados (mocks) para la respuesta.")

        # 3. Validación de Duplicados (Similitud Coseno)
        es_duplicado, titulo_original, similitud = (False, None, 0.0) # Mock: (False, 0.0, None) -> ajustado a (False, None, 0.0)

        if es_duplicado and similitud >= 0.80:
            return {
                "mensaje": "El archivo ya existe en la base de conocimiento.",
                "documento_original": titulo_original,
                "similitud": float(similitud)
            }

        # 4. Procesamiento de IA (Clasificación, Keywords, Resumen) - DATOS SIMULADOS
        categoria = "Documentación Técnica"
        probabilidad = 0.95
        contenido_relacionado = ["IA", "Backend", "OCI"]
        resumen_automatico = "Este es un resumen automático simulado."
        # ======================================================================
        # --- FIN: BLOQUE DE DATOS SIMULADOS (MOCKS) ---
        # ======================================================================

        # 5. Guardar en Base de Datos (Oracle Autonomous DB)
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

        # 6. Retorno de JSON Estructurado
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
        # Manejo específico para errores de valor, como texto no legible
        if str(ve) == "NO_TEXT":
            raise HTTPException(status_code=400, detail="El documento no contiene texto digital legible (posible escaneo) o está vacío.")
        raise HTTPException(status_code=400, detail=str(ve))

    except Exception as e:
        # Captura cualquier otra excepción no controlada
        tb_str = traceback.format_exc()
        print(f"--- TRACEBACK COMPLETO ---\n{tb_str}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno al procesar el archivo: {str(e)}\n\nTRACEBACK:\n{tb_str}"
        )
    finally:
        # Bloque de limpieza: Si se subió un archivo a OCI pero el proceso falló
        # (y no era un duplicado), se debe borrar el archivo huérfano.
        # La lógica de borrado ya no está en cada `except`, sino centralizada aquí.
        if url_archivo_oci:
            # Si la excepción que ocurrió no fue la de duplicado, borramos.
            # Este es un ejemplo simple, en un caso real podrías usar flags
            # para una lógica más compleja.
            # Por ahora, si hay excepción, limpiamos.
            print(f"Limpiando archivo huérfano de OCI: {url_archivo_oci}")
            await borrar_archivo_oci(url_archivo_oci)