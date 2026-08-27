import os
import oci
import uuid
import urllib.parse
from fastapi import UploadFile, HTTPException

async def subir_archivo_oci(file: UploadFile) -> str:
    """
    Autentica en OCI, sube el archivo físico al bucket y retorna su URL de referencia.
    """
    try:
        # 1. Autenticación Híbrida (Desarrollo Local vs Render)
        try:
            config = oci.config.from_file("~/.oci/config", "DEFAULT")
        except oci.exceptions.ConfigFileNotFound:
            config = {
                "user": os.getenv("OCI_USER"),
                "key_file": os.getenv("OCI_KEY_FILE_PATH"),
                "fingerprint": os.getenv("OCI_FINGERPRINT"),
                "tenancy": os.getenv("OCI_TENANCY"),
                "region": os.getenv("OCI_REGION")
            }

        # 2. Inicializar el cliente de Object Storage
        object_storage_client = oci.object_storage.ObjectStorageClient(config)

        # 3. Configuración del Bucket
        bucket_name = os.getenv("OCI_BUCKET_NAME")
        namespace = os.getenv("OCI_NAMESPACE")
        
        if not namespace:
            namespace = object_storage_client.get_namespace().data

        # 4. Generar nombre único
        extension = file.filename.split(".")[-1]
        nombre_unico = f"{uuid.uuid4()}.{extension}"

        # 5. Leer contenido
        file_content = await file.read()

        # 6. Ejecutar la subida física
        object_storage_client.put_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name=nombre_unico,
            put_object_body=file_content,
            content_type=file.content_type
        )

        # 7. Construir URL
        region_url = config.get("region", os.getenv("OCI_REGION"))
        url_referencia = f"https://objectstorage.{region_url}.oraclecloud.com/n/{namespace}/b/{bucket_name}/o/{nombre_unico}"

        return url_referencia

    except Exception as e:
        print(f"🛑 Error crítico en OCI al subir: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno al intentar guardar el documento en la nube de Oracle."
        )
    finally:
        # Reiniciar puntero de memoria
        await file.seek(0)


async def borrar_archivo_oci(url_archivo: str) -> bool:
    """
    Función de limpieza. Se conecta a OCI y elimina el archivo indicado.
    """
    try:
        # 1. Autenticación Híbrida
        try:
            config = oci.config.from_file("~/.oci/config", "DEFAULT")
        except oci.exceptions.ConfigFileNotFound:
            config = {
                "user": os.getenv("OCI_USER"),
                "key_file": os.getenv("OCI_KEY_FILE_PATH"),
                "fingerprint": os.getenv("OCI_FINGERPRINT"),
                "tenancy": os.getenv("OCI_TENANCY"),
                "region": os.getenv("OCI_REGION")
            }

        # 2. Extraer partes de la URL
        partes_url = url_archivo.split("/")
        
        try:
            idx_n = partes_url.index('n')
            idx_b = partes_url.index('b')
            idx_o = partes_url.index('o')
            
            namespace = partes_url[idx_n + 1]
            bucket_name = partes_url[idx_b + 1]
            object_name = urllib.parse.unquote("/".join(partes_url[idx_o + 1:]))
        except ValueError:
            print("🛑 Error: La URL proporcionada no tiene el formato estándar de OCI.")
            return False

        # 3. Inicializar el cliente y ejecutar borrado
        object_storage_client = oci.object_storage.ObjectStorageClient(config)

        object_storage_client.delete_object(
            namespace_name=namespace,
            bucket_name=bucket_name,
            object_name=object_name
        )

        print(f"🗑️ Éxito: Archivo '{object_name}' borrado correctamente de OCI.")
        return True

    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            print("⚠️ Advertencia: Se intentó borrar un archivo que ya no existe en OCI.")
            return True 
        print(f"🛑 Error de servicio en OCI al borrar: {str(e)}")
        return False
        
    except Exception as e:
        print(f"🛑 Error crítico intentando borrar en OCI: {str(e)}")
        return False