from sqlalchemy.orm import Session
from app.models import ContenidoProcesado

def guardar_documento_db(
    db: Session,
    titulo: str,
    texto: str,
    autor: str,
    categoria: str,
    probabilidad: float,
    resumen: str,
    tipo_archivo: str,
    url_archivo: str
) -> int:
    """
    Crea una nueva entrada en la tabla CONTENIDOS_PROCESADOS en la base de datos Oracle.

    Args:
        db (Session): La sesión de base de datos inyectada por FastAPI.
        titulo (str): El título del documento (ej. el nombre del archivo).
        texto (str): El contenido de texto completo extraído del archivo.
        autor (str): El autor del documento, si se proporciona.
        categoria (str): La categoría predicha por el modelo de IA.
        probabilidad (float): La probabilidad de la categoría predicha.
        resumen (str): El resumen automático del texto.
        tipo_archivo (str): La extensión del archivo (ej. 'pdf', 'txt').
        url_archivo (str): La URL pública del archivo en OCI Object Storage.

    Returns:
        int: El ID del registro recién creado en la base de datos.
    """
    # Se crea una instancia del modelo SQLAlchemy
    db_documento = ContenidoProcesado(
        titulo=titulo,
        texto=texto,
        autor=autor,
        categoria=categoria,
        probabilidad=probabilidad,
        resumen=resumen,
        tipo_archivo=tipo_archivo,
        url_archivo=url_archivo
    )
    
    # Se añade el objeto a la sesión
    db.add(db_documento)
    
    # Se confirman los cambios en la base de datos
    db.commit()
    
    # Se refresca el objeto para obtener el ID asignado por la BD
    db.refresh(db_documento)
    
    return db_documento.id
