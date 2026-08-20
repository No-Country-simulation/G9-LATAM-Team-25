import logging
import os

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session

from app.database import (
    get_db,
    crear_documento,
    obtener_documentos_existentes,
    obtener_documento_por_id,
    listar_documentos,
    buscar_documentos,
)
from app.utils.oci_storage import subir_archivo_oci, borrar_archivo_oci
from app.utils.extraccion import extraer_texto_plano
from app.ml_models.loader import (
    chequear_duplicado,
    predecir_categoria,
    generar_resumen,
    calcular_similitud_recomendaciones,
)
from app.schemas import (
    ClasificarTextoRequest,
    ClasificarTextoResponse,
    DocumentoResponse,
    ListaDocumentosResponse,
    DocumentoListadoResponse,
    RespuestaBusqueda,
    ResultadoBusqueda,
    RespuestaCargaArchivo,
    RespuestaCargaExitosa,
    RespuestaDuplicado,
    MetadatosResponse,
    ClasificacionResponse,
    DocumentoRelacionado,
    ContenidoResponse,
    DocumentoOriginalDuplicado,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================
# Configuración del endpoint (todo con valores por defecto
# razonables para MVP; nada de esto es obligatorio en el .env)
# ============================================================

FORMATOS_SOPORTADOS = (".pdf", ".txt")

# Tamaño máximo de archivo aceptado. Configurable con la variable
# de entorno opcional MAX_UPLOAD_SIZE_BYTES; por defecto 20 MB.
TAMANO_MAXIMO_ARCHIVO_BYTES = int(
    os.getenv("MAX_UPLOAD_SIZE_BYTES", str(20 * 1024 * 1024))
)

# Umbral de similitud para considerar un documento como duplicado
# exacto (bloquea el guardado). Configurable con UMBRAL_DUPLICADO.
UMBRAL_DUPLICADO = float(os.getenv("UMBRAL_DUPLICADO", "0.80"))

# Umbral (más bajo que el de duplicado) para considerar un documento
# como "relacionado" en la respuesta. Configurable con
# UMBRAL_CONTENIDO_RELACIONADO.
UMBRAL_CONTENIDO_RELACIONADO = float(
    os.getenv("UMBRAL_CONTENIDO_RELACIONADO", "0.30")
)

# Debajo de esta probabilidad, la respuesta marca
# "requiere_revision": true. Configurable con UMBRAL_REQUIERE_REVISION.
UMBRAL_REQUIERE_REVISION = float(os.getenv("UMBRAL_REQUIERE_REVISION", "0.60"))

MAX_PALABRAS_CLAVE = int(os.getenv("MAX_PALABRAS_CLAVE", "8"))
MAX_DOCUMENTOS_RELACIONADOS = int(os.getenv("MAX_DOCUMENTOS_RELACIONADOS", "5"))



# ============================================================
# CLASIFICACIÓN DIRECTA DE TEXTO
# ============================================================

@router.post(
    "/contenido/clasificar",
    response_model=ClasificarTextoResponse,
    status_code=status.HTTP_200_OK,
)
def clasificar_texto(
    payload: ClasificarTextoRequest,
):
    """
    Clasifica texto recibido directamente.

    No guarda el texto en Oracle: este endpoint es de inferencia.
    Utiliza el mismo modelo/vectorizador real que el flujo de carga.
    """
    categoria, probabilidad, palabras_clave = predecir_categoria(
        payload.texto,
        top_n_palabras_clave=payload.top_n_palabras_clave,
    )

    if categoria is None or probabilidad is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servicio de clasificación no está disponible en este momento.",
        )

    return ClasificarTextoResponse(
        categoria=categoria,
        probabilidad=probabilidad,
        palabras_clave=palabras_clave,
        requiere_revision=probabilidad < UMBRAL_REQUIERE_REVISION,
    )


# ============================================================
# LISTAR DOCUMENTOS
# ============================================================

@router.get(
    "/contenido",
    response_model=ListaDocumentosResponse,
    status_code=status.HTTP_200_OK,
)
def listar_contenido(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    categoria: str | None = Query(None),
    autor: str | None = Query(None),
    tipo_contenido: str | None = Query(None),
    db: Session = Depends(get_db),
):
    documentos, total = listar_documentos(
        db,
        offset=offset,
        limit=limit,
        categoria=categoria,
        autor=autor,
        tipo_contenido=tipo_contenido,
    )

    return ListaDocumentosResponse(
        items=[
            DocumentoListadoResponse.model_validate(documento)
            for documento in documentos
        ],
        total=total,
        offset=offset,
        limit=limit,
    )


# ============================================================
# BUSCAR DOCUMENTOS
# ============================================================

@router.get(
    "/buscar",
    response_model=RespuestaBusqueda,
    status_code=status.HTTP_200_OK,
)
def buscar_contenido(
    q: str | None = Query(None, description="Texto a buscar en el contenido y metadatos"),
    categoria: str | None = Query(None),
    autor: str | None = Query(None),
    tipo_contenido: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    documentos, total = buscar_documentos(
        db,
        q=q,
        categoria=categoria,
        autor=autor,
        tipo_contenido=tipo_contenido,
        offset=offset,
        limit=limit,
    )

    return RespuestaBusqueda(
        resultados=[
            ResultadoBusqueda.model_validate(documento)
            for documento in documentos
        ],
        total=total,
        query=q,
        filtros={
            "categoria": categoria,
            "autor": autor,
            "tipo_contenido": tipo_contenido,
        },
        offset=offset,
        limit=limit,
    )


# ============================================================
# OBTENER DOCUMENTO COMPLETO POR ID
# ============================================================

@router.get(
    "/contenido/{documento_id}",
    response_model=DocumentoResponse,
    status_code=status.HTTP_200_OK,
)
def obtener_contenido(
    documento_id: int,
    db: Session = Depends(get_db),
):
    documento = obtener_documento_por_id(db, documento_id)

    if documento is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe un documento con ID {documento_id}.",
        )

    return DocumentoResponse.model_validate(documento)


@router.post(
    "/contenido/archivo",
    status_code=status.HTTP_200_OK,
    response_model=RespuestaCargaArchivo,
)
async def procesar_archivo(
    file: UploadFile = File(...),
    autor: str = Form(...),
    tipo: str = Form(...),
    db: Session = Depends(get_db),
):
    # 1. Validación de formato (.pdf o .txt)
    if not file.filename.lower().endswith(FORMATOS_SOPORTADOS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Formato no soportado. Formatos permitidos: "
                f"{', '.join(FORMATOS_SOPORTADOS)}"
            ),
        )

    # 1b. Validación de tamaño (cuando el servidor puede determinarlo
    # sin tener que leer todo el archivo primero)
    tamano_declarado = getattr(file, "size", None)
    if (
        tamano_declarado is not None
        and tamano_declarado > TAMANO_MAXIMO_ARCHIVO_BYTES
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "El archivo supera el tamaño máximo permitido "
                f"({TAMANO_MAXIMO_ARCHIVO_BYTES // (1024 * 1024)} MB)."
            ),
        )

    url_archivo = None
    documento_guardado = None

    try:
        # 2. Subir archivo a OCI Object Storage
        url_archivo = await subir_archivo_oci(file)

        # 3. Extracción de texto
        try:
            texto_crudo = await extraer_texto_plano(file)

            if not texto_crudo or len(texto_crudo.strip()) == 0:
                raise ValueError(
                    "El archivo no tiene texto digital legible, "
                    "está vacío o es una imagen escaneada."
                )

        except Exception as error_extraccion:
            logger.warning(
                f"Fallo en la extracción de texto de '{file.filename}': "
                f"{error_extraccion}"
            )
            await borrar_archivo_oci(url_archivo)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fallo en la extracción de texto: {str(error_extraccion)}",
            )

        # 4. Obtener documentos existentes para comparar
        documentos_existentes = obtener_documentos_existentes(db)

        # 5. Chequeo de duplicados
        es_duplicado, similitud, id_original, titulo_original = chequear_duplicado(
            texto_crudo, documentos_existentes, umbral=UMBRAL_DUPLICADO
        )

        if es_duplicado:
            await borrar_archivo_oci(url_archivo)
            logger.info(
                f"Documento '{file.filename}' descartado por duplicado "
                f"(similitud={similitud:.2f}, original_id={id_original})."
            )
            return RespuestaDuplicado(
                mensaje="El archivo ya existe en la base de conocimientos.",
                documento_original=DocumentoOriginalDuplicado(
                    id=id_original,
                    titulo=titulo_original,
                ),
                similitud=similitud,
            )

        # 6. Clasificación: categoría + probabilidad + palabras clave
        categoria, probabilidad, palabras_clave = predecir_categoria(
            texto_crudo, top_n_palabras_clave=MAX_PALABRAS_CLAVE
        )

        if categoria is None or probabilidad is None:
            logger.error(
                f"El modelo de clasificación no pudo procesar '{file.filename}'."
            )
            await borrar_archivo_oci(url_archivo)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="El servicio de clasificación no está disponible en este momento.",
            )

        # 7. Resumen extractivo (algoritmo sin cambios, ya validado en la auditoría)
        resumen = generar_resumen(texto_crudo, n_oraciones=3, titulo=file.filename)

        # 8. Documentos relacionados (similares, pero no duplicados)
        similares = calcular_similitud_recomendaciones(
            texto_crudo,
            documentos_existentes,
            umbral=UMBRAL_CONTENIDO_RELACIONADO,
        )
        titulos_por_id = {
            doc["id"]: doc["titulo"] for doc in documentos_existentes
        }
        contenido_relacionado_respuesta = [
            DocumentoRelacionado(
                id=doc_id,
                titulo=titulos_por_id.get(doc_id),
                similitud=score,
            )
            for doc_id, score in similares[:MAX_DOCUMENTOS_RELACIONADOS]
        ]
        ids_relacionados = [doc_id for doc_id, _score in similares]

        # 9. Persistir en Oracle
        formato_archivo = file.filename.rsplit(".", 1)[-1].lower()

        try:
            documento_guardado = crear_documento(
                db,
                titulo=file.filename,
                texto=texto_crudo,
                autor=autor,
                categoria=categoria,
                probabilidad=probabilidad,
                resumen=resumen,
                palabras_clave=palabras_clave,
                contenido_relacionado=ids_relacionados,
                formato_archivo=formato_archivo,
                tipo_contenido=tipo,
                url_archivo=url_archivo,
            )
        except Exception as error_db:
            logger.error(
                f"Error guardando '{file.filename}' en Oracle: {error_db}"
            )
            await borrar_archivo_oci(url_archivo)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo guardar el documento en la base de datos.",
            )

        # 10. Construir y devolver la respuesta exitosa
        return RespuestaCargaExitosa(
            metadatos=MetadatosResponse(
                id=documento_guardado.id,
                titulo=documento_guardado.titulo,
                autor=documento_guardado.autor,
                formato_archivo=documento_guardado.formato_archivo,
                tipo_contenido=documento_guardado.tipo_contenido,
                url_archivo=documento_guardado.url_archivo,
            ),
            clasificacion=ClasificacionResponse(
                categoria=categoria,
                probabilidad=probabilidad,
                palabras_clave=palabras_clave,
                resumen=resumen,
                requiere_revision=probabilidad < UMBRAL_REQUIERE_REVISION,
            ),
            contenido_relacionado=contenido_relacionado_respuesta,
            contenido=ContenidoResponse(
                texto_extraido=texto_crudo,
                total_palabras=len(texto_crudo.split()),
            ),
        )

    except HTTPException:
        # Relanzar las excepciones HTTP que ya controlamos arriba
        raise

    except Exception:
        # Catch-all para cualquier otro error imprevisto (ej. caída de
        # OCI a mitad del flujo, error de red, etc). El detalle técnico
        # queda en el log; el cliente recibe un mensaje genérico.
        logger.exception(f"Error interno procesando '{file.filename}'.")
        if url_archivo and documento_guardado is None:
            # Solo limpiamos OCI si el documento NO llegó a guardarse;
            # si ya se guardó, el archivo en OCI sigue siendo válido.
            await borrar_archivo_oci(url_archivo)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor al procesar el archivo.",
        )
