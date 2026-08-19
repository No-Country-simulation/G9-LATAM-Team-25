from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel
from typing import List

# --- IMPORTACIONES ADAPTADAS A TU ARQUITECTURA (app/utils) ---
from app.utils.oci_storage import subir_archivo_oci, borrar_archivo_oci
from app.utils.extraccion import extraer_texto_plano
from app.ml_models.loader import chequear_duplicado, predecir_categoria,generar_resumen
from app.database import guardar_documento_db

router = APIRouter()

# Esquema de respuesta para Pydantic
class RespuestaCargaExitosa(BaseModel):
    id: int
    categoria: str
    probabilidad: float
    contenido_relacionado: List[str]
    autor: str
    tipo: str
    url_archivo: str
    resumen: str

@router.post("/contenido/archivo", status_code=status.HTTP_200_OK, response_model=RespuestaCargaExitosa)
async def procesar_archivo(
    file: UploadFile = File(...),
    autor: str = Form(...),
    tipo: str = Form(...)
):
    # 1. Validación de formato (.pdf o .txt)
    if not file.filename.lower().endswith(('.pdf', '.txt')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no soportado. Por favor sube un archivo .pdf o .txt"
        )

    url_archivo = None
    
    try:
        # 2. Subir archivo a OCI Object Storage
        # Asume que esta función retorna la URL pública/segura del archivo subido
        url_archivo = await subir_archivo_oci(file)

        # 3. y 4. Extracción de texto y Manejo de errores
        try:
            # Agregamos 'await' porque la lectura de archivos en memoria es asíncrona
            texto_crudo = await extraer_texto_plano(file)
            
            # Validación de texto vacío o imagen escaneada
            if not texto_crudo or len(texto_crudo.strip()) == 0:
                raise ValueError("El archivo no tiene texto digital legible, está vacío o es una imagen escaneada.")
                
        except Exception as e:
            # Si la extracción falla, hacemos ROLLBACK borrando el archivo de OCI
            if url_archivo:
                await borrar_archivo_oci(url_archivo)
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fallo en la extracción de texto: {str(e)}"
            )

        # 5. Ejecutar chequeo de similitud
        # Asume que esta función compara con la BD y devuelve un booleano y metadatos
        es_duplicado, similitud, titulo_original = chequear_duplicado(texto_crudo, umbral=0.80)

        if es_duplicado:
            # Cancelar flujo y limpiar OCI
            await borrar_archivo_oci(url_archivo)
            # Retornamos un diccionario directo; Pydantic lo validará o puedes usar un JSONResponse
            return {
                "mensaje": "Flujo cancelado: El archivo ya existe en la base de conocimientos.",
                "similitud": f"{similitud * 100:.2f}%",
                "titulo_original": titulo_original
            }

        # 6. Si NO es duplicado: Procesamiento de IA
        # Pasamos el texto por las funciones del modelo
        categoria, probabilidad, palabras_clave = predecir_categoria(texto_crudo)
        
        # Generamos el resumen extractivo automático explícitamente a 3 oraciones
        resumen = generar_resumen(texto_crudo, n_oraciones=3)

        # 7. Persistir en Oracle Autonomous Database
        # Se guarda toda la info y se recupera el ID generado por la BD
        registro_db = guardar_documento_db(
            titulo=file.filename,
            texto=texto_crudo,
            categoria=categoria,
            probabilidad=probabilidad,
            palabras_clave=palabras_clave,
            resumen=resumen,
            autor=autor,
            tipo=tipo,
            url_archivo=url_archivo
        )

        # 8. Retornar el JSON estructurado final
        return {
            "id": registro_db.id,
            "categoria": str(categoria), # Asegurar tipo nativo de Python para evitar error 500
            "probabilidad": float(probabilidad), # Mapeo seguro para Pydantic
            "contenido_relacionado": palabras_clave,
            "autor": autor,
            "tipo": tipo,
            "url_archivo": url_archivo,
            "resumen": resumen
        }

    except HTTPException:
        # Relanzar las excepciones HTTP que ya controlamos arriba (como el 400 del PDF vacío)
        raise
    except Exception as general_error:
        # Catch-all para cualquier otro error imprevisto (ej. caída de BD). 
        # Intentar borrar el archivo de OCI si se quedó huérfano
        if url_archivo:
             await borrar_archivo_oci(url_archivo)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(general_error)}"
        )