from fastapi import APIRouter, UploadFile, File, Query
# Asegúrate de importar ambas funciones de tu archivo de utilidades
from app.utils.oci_storage import subir_archivo_oci, borrar_archivo_oci

# LA LÍNEA MÁGICA: Creamos la variable "router"
router = APIRouter()

# ==========================================
# 1. ENDPOINT DE PRUEBA: SUBIDA A OCI
# ==========================================
@router.post("/test-oci-subir")
async def prueba_subida_oci(file: UploadFile = File(...)):
    """
    Endpoint temporal para validar la subida de archivos a Oracle Cloud.
    """
    try:
        # Ejecutamos la función de subida. 
        # (Si tu función subir_archivo_oci no tiene "async" en la definición, quítale el "await" aquí)
        url_generada = await subir_archivo_oci(file)
        
        return {
            "estado": "¡Subida exitosa! 🚀", 
            "url_en_oracle": url_generada
        }
    except Exception as e:
        return {
            "estado": "Fallo en la subida 🛑", 
            "error_detalle": str(e)
        }

# ==========================================
# 2. ENDPOINT DE PRUEBA: BORRADO EN OCI
# ==========================================
@router.delete("/test-oci-borrar")
async def prueba_borrado_oci(
    url_archivo: str = Query(..., description="Pega aquí la URL pública de Oracle Cloud que generaste en la prueba de subida")
):
    """
    Endpoint temporal solo para validar que el borrado en Oracle Cloud funcione correctamente.
    """
    try:
        # Ejecutamos la función de limpieza asíncrona
        exito = await borrar_archivo_oci(url_archivo)
        
        if exito:
            return {
                "estado": "¡Borrado exitoso! 🗑️", 
                "mensaje": "El archivo fue eliminado correctamente de tu bucket de Oracle."
            }
        else:
            return {
                "estado": "Fallo al intentar borrar ⚠️", 
                "mensaje": "Revisa la terminal de VS Code para ver el error exacto."
            }
    except Exception as e:
        return {
            "estado": "Error de conexión 🛑", 
            "error_detalle": str(e)
        }