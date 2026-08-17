import traceback
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.utils.oci_storage import subir_archivo_oci, borrar_archivo_oci
from app.crud import guardar_documento_db
from app.database import get_db
from app.utils.limpieza_de_texto import extraer_texto_pdf_txt, chequear_duplicado, generar_resumen
from app.ml_models.loader import load_model

router = APIRouter()

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
    subida_exitosa = False  # <-- BANDERA PARA CONTROLAR EL ROLLBACK EN FINALLY

    try:
        # 1. Subir archivo a OCI Object Storage
        url_archivo_oci = await subir_archivo_oci(archivo)

        # 2. Extracción de Texto Plano
        texto_crudo = await extraer_texto_pdf_txt(archivo)
        
        if not texto_crudo or len(texto_crudo.strip()) == 0:
            raise ValueError("NO_TEXT")

        # 3. Datos simulados (Mocks) mientras Data entrega el modelo
        es_duplicado, titulo_original, similitud = (False, None, 0.0)

        if es_duplicado and similitud >= 0.80:
            subida_exitosa = True # Marcamos como exitosa para no borrarlo en OCI
            return {
                "mensaje": "El archivo ya existe en la base de conocimiento.",
                "documento_original": titulo_original,
                "similitud": float(similitud)
            }

        categoria = "Documentación Técnica"
        probabilidad = 0.95
        contenido_relacionado = ["IA", "Backend", "OCI"]
        resumen_automatico = "Este es un resumen automático simulado."

        # 4. Guardar en Base de Datos Oracle
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

        subida_exitosa = True  # <-- MARCAMOS ÉXITO ANTES DE DEVOLVER LA RESPUESTA

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
        # SOLO LIMPIA DE OCI SI OCURRIÓ UN ERROR EN EL CAMINO
        if url_archivo_oci and not subida_exitosa:
            print(f"⚠️ Error detectado. Limpiando archivo huérfano de OCI: {url_archivo_oci}")
            await borrar_archivo_oci(url_archivo_oci)