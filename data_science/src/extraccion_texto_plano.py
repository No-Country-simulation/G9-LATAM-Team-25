import os
import re
import json
from typing import Tuple, Optional
from pypdf import PdfReader
from markitdown import MarkItDown

# Configuración y Límites
TAMANO_MAXIMO_MB = 5
EXTENSIONES_PERMITIDAS = (".pdf", ".txt")
PALABRAS_MINIMAS = 100
PALABRAS_MAXIMAS = 50_000

_PATRON_CARACTERES_CONTROL = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")
_PATRON_ESPACIOS_MULTIPLES = re.compile(r"\s+")
_PATRON_RUIDO_PAGINA = re.compile(
    r'^\s*(?:pág\.?|página)?\s*\d+\s*(?:de\s*\d+)?\s*$',
    re.IGNORECASE
)

def validar_archivo(file_path: str) -> Tuple[bool, str]:
    if not os.path.exists(file_path):
        return False, f"El archivo no existe: {file_path}"
    if not os.path.isfile(file_path):
        return False, f"La ruta no corresponde a un archivo: {file_path}"
    
    extension = os.path.splitext(file_path)[1].lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        return False, f"Extensión '{extension}' no permitida. Permitidas: {', '.join(EXTENSIONES_PERMITIDAS)}"
    
    tamano_bytes = os.path.getsize(file_path)
    if tamano_bytes == 0:
        return False, "El archivo está vacío o corrupto."
    
    tamano_mb = tamano_bytes / (1024 * 1024)
    if tamano_mb > TAMANO_MAXIMO_MB:
        return False, f"El archivo supera el máximo ({TAMANO_MAXIMO_MB} MB). Actual: {tamano_mb:.2f} MB."
    
    if extension == ".pdf":
        try:
            lector = PdfReader(file_path)
            if len(lector.pages) == 0:
                return False, "El PDF no contiene páginas o está corrupto."
        except Exception as e:
            return False, f"El PDF está corrupto o no se pudo abrir: {e}"
            
    return True, "Archivo válido."

def _extraer_metadata_estructural(file_path: str, md_text: str) -> dict:
    extension = os.path.splitext(file_path)[1].lower()
    tipo_archivo = extension.replace(".", "")
    paginas: Optional[int] = None
    posee_imagenes = False

    if extension == ".pdf":
        try:
            lector = PdfReader(file_path)
            paginas = len(lector.pages)
            for pagina in lector.pages:
                try:
                    if len(pagina.images) > 0:
                        posee_imagenes = True
                        break
                except Exception:
                    continue
        except Exception:
            paginas = None

    posee_tablas = bool(
        re.search(r"^\s*\|.+\|\s*$", md_text, re.MULTILINE)
    )

    return {
        "tipo_archivo": tipo_archivo,
        "paginas": paginas,
        "posee_tablas": posee_tablas,
        "posee_imagenes": posee_imagenes,
    }

def extraer_markdown(file_path: str) -> Tuple[str, dict]:
    extension = os.path.splitext(file_path)[1].lower()
    if extension == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            md_text = f.read()
    else:
        convertidor = MarkItDown()
        resultado = convertidor.convert(file_path)
        md_text = resultado.text_content

    metadata = _extraer_metadata_estructural(file_path, md_text)
    return md_text, metadata

def normalizar_texto(md_text: str) -> str:
    """
    Normaliza el texto a un flujo plano contiguo (sin saltos de línea):
    - Elimina caracteres de control y nulos.
    - Filtra encabezados/pies de página tipo 'Página X de Y'.
    - Une todo el contenido en una única cadena separada por espacios simples.
    """
    if not md_text:
        return ""

    # 1. Limpieza inicial de caracteres no imprimibles/control
    texto = md_text.replace("\x00", "")
    texto = _PATRON_CARACTERES_CONTROL.sub("", texto)

    # 2. División por líneas para remover ruido de paginación
    lineas = texto.splitlines()
    lineas_limpias = []
    
    for linea in lineas:
        linea_str = linea.strip()
        if not linea_str:
            continue
        # Ignorar líneas que sean únicamente numeración de página
        if _PATRON_RUIDO_PAGINA.match(linea_str):
            continue
        # Remover sintaxis Markdown de títulos (#) y viñetas para texto plano puro
        linea_str = re.sub(r'^[#*•\-]+\s*', '', linea_str)
        lineas_limpias.append(linea_str)

    # 3. Colapsar en una sola secuencia de texto plano
    texto_unido = " ".join(lineas_limpias)
    return _PATRON_ESPACIOS_MULTIPLES.sub(" ", texto_unido).strip()

def validar_contenido(texto: str) -> Tuple[bool, str]:
    if not texto or not texto.strip():
        return False, "El texto extraído está vacío o no es legible."

    total_palabras = len(texto.split())
    if total_palabras < PALABRAS_MINIMAS:
        return False, f"Muy pocas palabras ({total_palabras}). Mínimo: {PALABRAS_MINIMAS}."
    if total_palabras > PALABRAS_MAXIMAS:
        return False, f"Excede el máximo de palabras ({total_palabras} > {PALABRAS_MAXIMAS})."

    return True, "Contenido válido."

def procesar_documento(file_path: str) -> dict:
    es_valido, mensaje = validar_archivo(file_path)
    if not es_valido:
        return {"estado": "error", "mensaje": mensaje}

    try:
        md_text, metadata = extraer_markdown(file_path)
    except Exception as e:
        return {"estado": "error", "mensaje": f"Error en extracción: {e}"}

    texto_normalizado = normalizar_texto(md_text)

    es_valido_contenido, mensaje_contenido = validar_contenido(texto_normalizado)
    if not es_valido_contenido:
        return {"estado": "error", "mensaje": mensaje_contenido}

    return {
        "estado": "success",
        "documento": {
            "nombre_archivo": os.path.basename(file_path),
            "tipo_archivo": metadata["tipo_archivo"],
            "paginas": metadata["paginas"],
        },
        "extraccion": {
            "texto_extraido": texto_normalizado,
            "total_palabras": len(texto_normalizado.split()),
            "total_caracteres": len(texto_normalizado),
        },
        "metadata_estructural": {
            "posee_tablas": metadata["posee_tablas"],
            "posee_imagenes": metadata["posee_imagenes"],
        },
    }

if __name__ == "__main__":
    # --- PRUEBAS LOCALES Y SIMULACIÓN ---
    import sys

    # Cambia esto por la ruta de un PDF o TXT de prueba que tengas localmente
    archivo_prueba = ""

    print("=== INICIANDO PRUEBA DEL PIPELINE DE EXTRACCIÓN ===")
    
    if os.path.exists(archivo_prueba):
        resultado = procesar_documento(archivo_prueba)
        print("\n[RESULTADO JSON QUE RECIBIRÁ EL BACKEND / FRONTEND]:")
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        print(f"\n[Aviso]: Coloca un archivo de prueba llamado '{archivo_prueba}' en el mismo directorio para ejecutar la simulación.")