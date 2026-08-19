# app/ml_models/loader.py

import os
import logging
import joblib
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity

# Funciones del módulo de resumen
from utils.texto_visible import extraer_texto_visible


logger = logging.getLogger(__name__)


# ============================================================
# RUTAS DE LOS MODELOS
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "modelo.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "vectorizer.pkl")


# ============================================================
# CARGA DE MODELOS
# ============================================================

def load_model():
    """
    Carga el modelo y el vectorizador previamente entrenados.

    Returns:
        tuple:
            (modelo, vectorizador)

        Si ocurre un error, retorna:
            (None, None)
    """

    try:
        modelo = joblib.load(MODEL_PATH)
        vectorizador = joblib.load(VECTORIZER_PATH)

        logger.info(
            "Modelo y vectorizador cargados exitosamente."
        )

        return modelo, vectorizador

    except FileNotFoundError as e:

        logger.error(
            f"Error cargando los modelos: {e}. "
            "Asegúrate de que los archivos .pkl existan."
        )

        return None, None

    except Exception as e:

        logger.error(
            f"Error inesperado cargando los modelos: {e}"
        )

        return None, None


# ============================================================
# CARGA ÚNICA
# ============================================================

modelo, vectorizador = load_model()


# ============================================================
# CALCULAR SIMILITUD PARA RECOMENDACIONES
# ============================================================

def calcular_similitud_recomendaciones(
    texto_nuevo: str,
    documentos_db: list,
    umbral: float = 0.80
) -> list[int]:
    """
    Busca documentos similares al texto nuevo utilizando
    el vectorizador TF-IDF previamente entrenado.

    documentos_db:

    [
        {
            "id": 12,
            "texto": "Contenido del documento..."
        },
        ...
    ]

    Returns:
        Lista con los IDs de los documentos similares.
    """

    if not documentos_db:
        return []

    if vectorizador is None:
        logger.error(
            "No se puede calcular similitud: "
            "el vectorizador no fue cargado."
        )
        return []

    try:

        textos_existentes = [
            doc["texto"]
            for doc in documentos_db
        ]

        ids_existentes = [
            doc["id"]
            for doc in documentos_db
        ]

        # Transformar el texto nuevo utilizando
        # el vectorizador previamente entrenado.
        vector_nuevo = vectorizador.transform(
            [texto_nuevo]
        )

        # Transformar los documentos existentes
        matriz_documentos = vectorizador.transform(
            textos_existentes
        )

        # Calcular similitud coseno
        similitudes = cosine_similarity(
            vector_nuevo,
            matriz_documentos
        ).flatten()

        # Obtener documentos que superan el umbral
        ids_similares = [
            ids_existentes[i]
            for i, score in enumerate(similitudes)
            if score >= umbral
        ]

        return ids_similares

    except Exception as e:

        logger.error(
            f"Error calculando similitud para recomendaciones: {e}"
        )

        return []


# ============================================================
# CHEQUEAR DOCUMENTO DUPLICADO
# ============================================================

def chequear_duplicado(
    texto_crudo: str,
    documentos_db: list,
    umbral: float = 0.80
) -> tuple:
    """
    Verifica si un documento ya existe en la base de datos.

    documentos_db:

    [
        {
            "titulo": "Doc 1",
            "texto": "Contenido del documento..."
        },
        ...
    ]

    Returns:
        (
            es_duplicado: bool,
            similitud: float,
            titulo_original: str
        )
    """

    if not documentos_db:
        return False, 0.0, ""

    if vectorizador is None:
        logger.error(
            "No se puede verificar duplicados: "
            "el vectorizador no fue cargado."
        )

        return False, 0.0, ""

    try:

        textos_existentes = [
            doc["texto"]
            for doc in documentos_db
        ]

        titulos_existentes = [
            doc["titulo"]
            for doc in documentos_db
        ]

        # Transformar el nuevo documento
        vector_nuevo = vectorizador.transform(
            [texto_crudo]
        )

        # Transformar documentos existentes
        matriz_documentos = vectorizador.transform(
            textos_existentes
        )

        # Calcular similitud coseno
        similitudes = cosine_similarity(
            vector_nuevo,
            matriz_documentos
        ).flatten()

        # Obtener índice del documento más parecido
        indice_max_similitud = np.argmax(
            similitudes
        )

        max_similitud = float(
            similitudes[indice_max_similitud]
        )

        # Verificar si supera el umbral
        if max_similitud >= umbral:

            titulo_original = titulos_existentes[
                indice_max_similitud
            ]

            return (
                True,
                max_similitud,
                titulo_original
            )

        return (
            False,
            max_similitud,
            ""
        )

    except Exception as e:

        logger.error(
            f"Error verificando documento duplicado: {e}"
        )

        return False, 0.0, ""


# ============================================================
# RESUMEN EXTRACTIVO
# ============================================================

# Configuración del algoritmo MMR
_PESO_RELEVANCIA_MMR = 0.65
_PESO_TITULO = 0.15

_MARCADOR_PUNTO = "\ue000"
_MARCADOR_ORACION = "\ue001"

_MAX_PALABRAS_UNIDAD = 35
_MAX_CARACTERES_UNIDAD = 320
_MAX_CARACTERES_DOCUMENTO_COMPLETO = 500


# ============================================================
# STOPWORDS ESPAÑOL
# ============================================================

_STOPWORDS_ES = frozenset(
    """
    de la que el en y a los del se las por un para con no una su al lo como
    más pero sus le ya o este sí porque esta entre cuando muy sin sobre también
    me hasta hay donde quien desde todo nos durante todos uno les ni contra
    otros ese eso ante ellos e esto mí antes algunos qué unos yo otro otras
    otra él tanto esa estos mucho quienes nada muchos cual poco ella estar
    estas algunas algo nosotros mi mis tú te ti tu tus ellas nosotras vosotros
    vosotras os mío mía míos mías tuyo tuya tuyos tuyas suyo suya suyos suyas
    nuestro nuestra nuestros nuestras vuestro vuestra vuestros vuestras esos
    esas estoy estás está estamos estáis están esté estés estemos estéis estén
    estaré estarás estará estaremos estaréis estarán estaría estarías estaríamos
    estaríais estarían estaba estabas estábamos estabais estaban estuve
    estuviste estuvo estuvimos estuvisteis estuvieron estuviera estuvieras
    estuviéramos estuvierais estuvieran estuviese estuvieses estuviésemos
    estuvieseis estuviesen estando estado estada estados estadas estad he has ha
    hemos habéis han haya hayas hayamos hayáis hayan habré habrás habrá habremos
    habréis habrán habría habrías habríamos habríais habrían había habías
    habíamos habíais habían hube hubiste hubo hubimos hubisteis hubieron hubiera
    hubieras hubiéramos hubierais hubieran hubiese hubieses hubiésemos hubieseis
    hubiesen habiendo habido habida habidos habidas soy eres es somos sois son
    sea seas seamos seáis sean seré serás será seremos seréis serán sería serías
    seríamos seríais serían era eras éramos erais eran fui fuiste fue fuimos
    fuisteis fueron fuera fueras fuéramos fuerais fueran fuese fueses fuésemos
    fueseis fuesen sintiendo sentido sentida sentidos sentidas siente sentid
    tengo tienes tiene tenemos tenéis tienen tenga tengas tengamos tengáis
    tengan tendré tendrás tendrá tendremos tendréis tendrán tendría tendrías
    tendríamos tendríais tendrían tenía tenías teníamos teníais tenían tuve
    tuviste tuvo tuvimos tuvisteis tuvieron tuviera tuvieras tuviéramos
    tuvierais tuvieran tuviese tuvieses tuviésemos tuvieseis tuviesen teniendo
    tenido tenida tenidos tenidas tened
    """.split()
)


# ============================================================
# PATRONES PARA DIVIDIR ORACIONES
# ============================================================

import re
from math import ceil


_PATRON_EJEMPLO = re.compile(
    r"\bp\.\s*ej\.",
    flags=re.IGNORECASE
)

_PATRONES_ABREVIATURAS_COMPUESTAS = (
    re.compile(r"\bee\.\s*uu\.", flags=re.IGNORECASE),
    re.compile(
        r"\b(?:a|d)\.\s*c\.",
        flags=re.IGNORECASE
    ),
)

_PATRON_TRATAMIENTO = re.compile(
    r"\b(?:sr|sra|srta|dr|dra|ing|lic|prof|profa|ud|uds)\.",
    flags=re.IGNORECASE
)

_PATRON_ABREVIATURA_CONTEXTO = re.compile(
    r"\b(?:etc|núm|nro|pág|págs|aprox|tel|vol|cap|art|arts)\.",
    flags=re.IGNORECASE
)

_PATRON_INICIAL = re.compile(
    r"\b[A-ZÁÉÍÓÚÜÑ]\.(?=\s+[A-ZÁÉÍÓÚÜÑ])"
)

_PATRON_LIMITE = re.compile(
    r"(?P<puntuacion_cierre>[.!?]+)"
    r"(?P<cierres>['\"»”’)\]]+)"
    r"(?=\s+|$|\ue001|[¿¡«“‘A-ZÁÉÍÓÚÜÑ])"
    r"|(?P<puntuacion>[.!?]+)"
    r"(?=\s+|$|\ue001|[¿¡'\"«“‘A-ZÁÉÍÓÚÜÑ])"
)

_PATRON_CPLUSPLUS = re.compile(
    r"(?<!\w)c\+\+(?!\w)",
    flags=re.IGNORECASE
)

_PATRON_CSHARP = re.compile(
    r"(?<!\w)c#(?!\w)",
    flags=re.IGNORECASE
)

_PATRON_DOTNET = re.compile(
    r"\.net\b",
    flags=re.IGNORECASE
)

_PATRON_VINETA = re.compile(
    r"^(?:[-*•‣▪]|\d+[.)])\s+"
)

_INICIOS_ORACION_COMUNES = frozenset(
    """
    además ahora allí aunque así cuando después el ella ellas ellos en entonces
    esa esas ese esos esta estas este estos finalmente la las luego los mientras
    no nosotros por primero segundo sin también un una unas unos
    """.split()
)


# ============================================================
# VALIDACIÓN
# ============================================================

def _validar_parametros(
    texto: str,
    n_oraciones: int,
    titulo: str | None,
) -> None:

    if not isinstance(texto, str):
        raise TypeError(
            "texto debe ser una cadena de caracteres"
        )

    if (
        isinstance(n_oraciones, bool)
        or not isinstance(n_oraciones, int)
    ):
        raise TypeError(
            "n_oraciones debe ser un entero"
        )

    if n_oraciones < 1:
        raise ValueError(
            "n_oraciones debe ser mayor o igual que 1"
        )

    if titulo is not None and not isinstance(titulo, str):
        raise TypeError(
            "titulo debe ser una cadena de caracteres o None"
        )


# ============================================================
# NORMALIZACIÓN
# ============================================================

def _normalizar_espacios(texto: str) -> str:

    sin_controles = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
        " ",
        texto
    )

    return " ".join(
        sin_controles.split()
    )


def _parece_lista_sin_marcadores(
    lineas: list[str]
) -> bool:

    return len(lineas) > 1 and all(
        len(linea.split()) <= 12
        and (
            linea[0].isupper()
            or linea[0].isdigit()
        )
        and linea[-1] not in ",;:-"
        for linea in lineas
    )


def _normalizar_bloques(texto: str) -> list[str]:

    sin_marcadores = (
        texto
        .replace(_MARCADOR_PUNTO, " ")
        .replace(_MARCADOR_ORACION, " ")
    )

    sin_controles = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
        " ",
        sin_marcadores
    )

    normalizado = (
        sin_controles
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

    normalizado = re.sub(
        r"[ \t]{3,}",
        "\n\n",
        normalizado
    )

    grupos = re.split(
        r"\n\s*\n",
        normalizado
    )

    bloques: list[str] = []

    for grupo in grupos:

        lineas = [
            " ".join(linea.split())
            for linea in grupo.split("\n")
            if linea.strip()
        ]

        if not lineas:
            continue

        if _parece_lista_sin_marcadores(lineas):

            bloques.extend(lineas)
            continue

        parrafo: list[str] = []

        for linea in lineas:

            if _PATRON_VINETA.match(linea):

                if parrafo:
                    bloques.append(
                        " ".join(parrafo)
                    )
                    parrafo = []

                bloques.append(linea)

            else:

                parrafo.append(linea)

        if parrafo:
            bloques.append(
                " ".join(parrafo)
            )

    return bloques


# ============================================================
# PROTECCIÓN DE ABREVIATURAS
# ============================================================

def _proteger_abreviatura_compuesta(
    coincidencia: re.Match[str]
) -> str:

    abreviatura = coincidencia.group(0)

    partes = abreviatura.rsplit(
        ".",
        maxsplit=1
    )

    internos = partes[0].replace(
        ".",
        _MARCADOR_PUNTO
    )

    if len(partes) == 1:
        return internos

    resto = coincidencia.string[
        coincidencia.end():
    ]

    siguiente = re.search(
        r"\S+",
        resto
    )

    if siguiente is None:

        continua = False

    else:

        token = (
            siguiente.group(0)
            .strip(
                "¿¡'\"«»“”‘’()[]{}.,;:"
            )
            .casefold()
        )

        primer_caracter = siguiente.group(0)[0]

        continua = (
            primer_caracter.islower()
            or primer_caracter.isdigit()
            or primer_caracter in ",;:"
            or token not in _INICIOS_ORACION_COMUNES
        )

    punto_final = (
        _MARCADOR_PUNTO
        if continua
        else "."
    )

    return f"{internos}{punto_final}"


def _proteger_todos_los_puntos(
    coincidencia: re.Match[str]
) -> str:

    return coincidencia.group(0).replace(
        ".",
        _MARCADOR_PUNTO
    )


def _proteger_abreviatura_segun_contexto(
    coincidencia: re.Match[str]
) -> str:

    abreviatura = coincidencia.group(0)

    resto = coincidencia.string[
        coincidencia.end():
    ]

    siguiente = re.search(
        r"\S",
        resto
    )

    if siguiente is None:
        return abreviatura

    caracter = siguiente.group(0)

    if (
        caracter.islower()
        or caracter.isdigit()
        or caracter in ",;:"
    ):
        return abreviatura.replace(
            ".",
            _MARCADOR_PUNTO
        )

    return abreviatura


# ============================================================
# MARCAR LÍMITES DE ORACIONES
# ============================================================

def _marcar_limite_oracion(
    coincidencia: re.Match[str]
) -> str:

    puntuacion = (
        coincidencia.group(
            "puntuacion_cierre"
        )
        or coincidencia.group(
            "puntuacion"
        )
    )

    cierres = (
        coincidencia.group("cierres")
        or ""
    )

    siguiente = coincidencia.string[
        coincidencia.end():
        coincidencia.end() + 1
    ]

    if (
        cierres.startswith(
            ('"', "'")
        )
        and siguiente
        and siguiente != _MARCADOR_ORACION
        and not siguiente.isspace()
    ):

        comilla = cierres[0]

        anteriores = coincidencia.string[
            :coincidencia.start()
        ]

        posiciones = re.finditer(
            rf"(?<!\\){re.escape(comilla)}",
            anteriores
        )

        if comilla == "'":

            cantidad_abiertas = sum(
                not (
                    coincidencia.start() > 0
                    and coincidencia.end()
                    < len(anteriores)
                    and anteriores[
                        coincidencia.start() - 1
                    ].isalnum()
                    and anteriores[
                        coincidencia.end()
                    ].isalnum()
                )
                for coincidencia in posiciones
            )

        else:

            cantidad_abiertas = sum(
                1
                for _ in posiciones
            )

        if cantidad_abiertas % 2 == 0:

            return (
                f"{puntuacion}"
                f"{_MARCADOR_ORACION}"
                f"{cierres}"
            )

    return (
        f"{puntuacion}"
        f"{cierres}"
        f"{_MARCADOR_ORACION}"
    )


# ============================================================
# PREPROCESAMIENTO TF-IDF
# ============================================================

def _preprocesar_tfidf(
    texto: str
) -> str:

    normalizado = texto.casefold()

    normalizado = _PATRON_CPLUSPLUS.sub(
        " cplusplus ",
        normalizado
    )

    normalizado = _PATRON_CSHARP.sub(
        " csharp ",
        normalizado
    )

    return _PATRON_DOTNET.sub(
        " dotnet ",
        normalizado
    )


# ============================================================
# FRAGMENTAR UNIDADES LARGAS
# ============================================================

def _fragmentar_unidad_larga(
    unidad: str
) -> list[str]:

    coincidencias = list(
        re.finditer(
            r"\S+",
            unidad
        )
    )

    if not coincidencias:
        return []

    cantidad_fragmentos = max(
        ceil(
            len(coincidencias)
            / _MAX_PALABRAS_UNIDAD
        ),
        ceil(
            len(unidad)
            / _MAX_CARACTERES_UNIDAD
        ),
    )

    if cantidad_fragmentos <= 1:
        return [unidad]

    cantidad_fragmentos = min(
        cantidad_fragmentos,
        len(coincidencias)
    )

    if cantidad_fragmentos <= 1:
        return [unidad]

    base, sobrantes = divmod(
        len(coincidencias),
        cantidad_fragmentos
    )

    fragmentos: list[str] = []

    inicio_palabra = 0

    for indice in range(
        cantidad_fragmentos
    ):

        palabras_fragmento = (
            base
            + (
                1
                if indice < sobrantes
                else 0
            )
        )

        fin_palabra = (
            inicio_palabra
            + palabras_fragmento
        )

        inicio_caracter = coincidencias[
            inicio_palabra
        ].start()

        fin_caracter = coincidencias[
            fin_palabra - 1
        ].end()

        fragmentos.append(
            unidad[
                inicio_caracter:fin_caracter
            ].strip()
        )

        inicio_palabra = fin_palabra

    resultado: list[str] = []

    for fragmento in fragmentos:

        subfragmentos = (
            _fragmentar_unidad_larga(
                fragmento
            )
        )

        if subfragmentos == [fragmento]:
            resultado.append(fragmento)

        else:
            resultado.extend(
                subfragmentos
            )

    return resultado


# ============================================================
# DIVISIÓN DE ORACIONES
# ============================================================

def _dividir_oraciones_base(
    texto: str,
    *,
    fragmentar_largos: bool,
) -> list[str]:

    bloques = _normalizar_bloques(texto)

    if not bloques:
        return []

    bloques_protegidos = [
        re.sub(
            r"^(\d+)\.(?=\s)",
            lambda coincidencia:
                f"{coincidencia.group(1)}"
                f"{_MARCADOR_PUNTO}",
            bloque,
        )
        for bloque in bloques
    ]

    texto_limpio = _MARCADOR_ORACION.join(
        bloques_protegidos
    )

    protegido = re.sub(
        r"(?<=\d)\.(?=\d)",
        _MARCADOR_PUNTO,
        texto_limpio
    )

    protegido = _PATRON_EJEMPLO.sub(
        _proteger_todos_los_puntos,
        protegido
    )

    for patron in _PATRONES_ABREVIATURAS_COMPUESTAS:

        protegido = patron.sub(
            _proteger_abreviatura_compuesta,
            protegido
        )

    protegido = _PATRON_DOTNET.sub(
        lambda coincidencia:
            coincidencia.group(0).replace(
                ".",
                _MARCADOR_PUNTO,
                1,
            ),
        protegido,
    )

    protegido = _PATRON_TRATAMIENTO.sub(
        _proteger_abreviatura_compuesta,
        protegido
    )

    protegido = _PATRON_ABREVIATURA_CONTEXTO.sub(
        _proteger_abreviatura_segun_contexto,
        protegido
    )

    protegido = _PATRON_INICIAL.sub(
        _proteger_abreviatura_compuesta,
        protegido
    )

    marcado = _PATRON_LIMITE.sub(
        _marcar_limite_oracion,
        protegido
    )

    oraciones: list[str] = []

    for fragmento in marcado.split(
        _MARCADOR_ORACION
    ):

        restaurado = (
            fragmento
            .replace(
                _MARCADOR_PUNTO,
                "."
            )
            .strip()
        )

        if restaurado:

            if fragmentar_largos:

                oraciones.extend(
                    _fragmentar_unidad_larga(
                        restaurado
                    )
                )

            else:

                oraciones.append(
                    restaurado
                )

    return oraciones


def _dividir_texto_visible(
    texto_visible: str
) -> list[str]:

    unidades = _dividir_oraciones_base(
        texto_visible,
        fragmentar_largos=True
    )

    for _ in range(4):

        estabilizadas: list[str] = []

        hubo_cambios = False

        for unidad in unidades:

            partes = _dividir_oraciones_base(
                unidad,
                fragmentar_largos=False
            )

            if partes != [unidad]:
                hubo_cambios = True

            estabilizadas.extend(partes)

        unidades = estabilizadas

        if not hubo_cambios:
            break

    return unidades


def dividir_oraciones(
    texto: str
) -> list[str]:
    """
    Divide texto español en unidades extractivas estables.
    """

    if not isinstance(texto, str):
        raise TypeError(
            "texto debe ser una cadena de caracteres"
        )

    return _dividir_texto_visible(
        extraer_texto_visible(texto)
    )


# ============================================================
# ELIMINAR DUPLICADOS DEL RESUMEN
# ============================================================

def _eliminar_oraciones_duplicadas(
    oraciones: list[str]
) -> list[str]:

    resultado: list[str] = []

    claves_vistas: set[str] = set()

    for oracion in oraciones:

        clave_lexica = " ".join(
            re.findall(
                r"\w+",
                _preprocesar_tfidf(
                    oracion
                )
            )
        )

        clave = (
            clave_lexica
            or oracion.casefold().strip()
        )

        if (
            clave
            and clave not in claves_vistas
        ):

            claves_vistas.add(clave)

            resultado.append(
                oracion
            )

    return resultado


# ============================================================
# RELEVANCIA
# ============================================================

def _calcular_relevancia(
    matriz_tfidf,
    titulo: str | None,
    vectorizador_resumen
):

    centroide = (
        matriz_tfidf
        .mean(axis=0)
        .A
    )

    relevancia = cosine_similarity(
        matriz_tfidf,
        centroide
    ).ravel()

    titulo_limpio = _normalizar_espacios(
        extraer_texto_visible(
            titulo or ""
        )
    )

    if titulo_limpio:

        vector_titulo = (
            vectorizador_resumen.transform(
                [titulo_limpio]
            )
        )

        if vector_titulo.nnz:

            similitud_titulo = cosine_similarity(
                matriz_tfidf,
                vector_titulo
            ).ravel()

            relevancia = (
                (1.0 - _PESO_TITULO)
                * relevancia
                + _PESO_TITULO
                * similitud_titulo
            )

    return relevancia


# ============================================================
# SELECCIÓN MMR
# ============================================================

def _seleccionar_con_mmr(
    matriz_tfidf,
    relevancia,
    cantidad: int
) -> list[int]:

    candidatos = list(
        range(
            matriz_tfidf.shape[0]
        )
    )

    primero = max(
        candidatos,
        key=lambda indice:
            (
                relevancia[indice],
                -indice
            )
    )

    seleccionados = [primero]

    candidatos.remove(primero)

    while (
        candidatos
        and len(seleccionados)
        < cantidad
    ):

        similitudes = cosine_similarity(
            matriz_tfidf[candidatos],
            matriz_tfidf[seleccionados]
        ).max(axis=1)

        def clave(
            indice_local: int
        ):

            indice_oracion = (
                candidatos[indice_local]
            )

            puntuacion_mmr = (
                _PESO_RELEVANCIA_MMR
                * float(
                    relevancia[
                        indice_oracion
                    ]
                )
                -
                (1.0 - _PESO_RELEVANCIA_MMR)
                * float(
                    similitudes[
                        indice_local
                    ]
                )
            )

            return (
                puntuacion_mmr,
                float(
                    relevancia[
                        indice_oracion
                    ]
                ),
                -indice_oracion,
            )

        mejor_local = max(
            range(len(candidatos)),
            key=clave
        )

        seleccionados.append(
            candidatos.pop(
                mejor_local
            )
        )

    return seleccionados


# ============================================================
# UNIR UNIDADES
# ============================================================

def _unir_unidades(
    unidades: list[str],
    limite: int
) -> str:

    seleccionadas = unidades[:limite]

    como_parrafo = " ".join(
        seleccionadas
    )

    if (
        _dividir_texto_visible(
            como_parrafo
        )
        == seleccionadas
    ):

        return como_parrafo

    por_bloques = "\n\n".join(
        seleccionadas
    )

    if (
        _dividir_texto_visible(
            por_bloques
        )
        == seleccionadas
    ):

        return por_bloques

    reparadas = (
        _dividir_texto_visible(
            por_bloques
        )[:limite]
    )

    return "\n\n".join(
        reparadas
    )


# ============================================================
# GENERAR RESUMEN
# ============================================================

def generar_resumen(
    texto: str,
    n_oraciones: int = 3,
    *,
    titulo: str | None = None,
) -> str:
    """
    Genera un resumen extractivo utilizando:

    - TF-IDF
    - Similitud coseno
    - Relevancia respecto al centroide
    - Relevancia respecto al título
    - MMR para evitar redundancia

    La función conserva el algoritmo especializado
    de resumen y no utiliza el vectorizer.pkl general,
    ya que necesita configuraciones específicas.
    """

    _validar_parametros(
        texto,
        n_oraciones,
        titulo
    )

    texto_visible = (
        extraer_texto_visible(texto)
    )

    oraciones_originales = (
        _dividir_texto_visible(
            texto_visible
        )
    )

    if not oraciones_originales:
        return ""

    longitud_visible = len(
        _normalizar_espacios(
            texto_visible
        )
    )

    if (
        len(oraciones_originales)
        <= n_oraciones
        and longitud_visible
        <= _MAX_CARACTERES_DOCUMENTO_COMPLETO
    ):

        return _unir_unidades(
            oraciones_originales,
            n_oraciones
        )

    oraciones = (
        _eliminar_oraciones_duplicadas(
            oraciones_originales
        )
    )

    cantidad = min(
        n_oraciones,
        len(oraciones)
    )

    if (
        len(oraciones)
        <= n_oraciones
        and longitud_visible
        > _MAX_CARACTERES_DOCUMENTO_COMPLETO
        and cantidad > 1
    ):

        cantidad -= 1

    if len(oraciones) <= cantidad:

        return _unir_unidades(
            oraciones,
            cantidad
        )

    # IMPORTANTE:
    # Este vectorizador es específico para el resumen.
    from sklearn.feature_extraction.text import TfidfVectorizer

    vectorizador_resumen = TfidfVectorizer(
        lowercase=False,
        preprocessor=_preprocesar_tfidf,
        stop_words=sorted(
            _STOPWORDS_ES
        ),
        ngram_range=(1, 2),
        sublinear_tf=True,
        token_pattern=r"(?u)\b\w+\b",
    )

    try:

        matriz_tfidf = (
            vectorizador_resumen
            .fit_transform(oraciones)
        )

    except ValueError as error:

        if (
            "empty vocabulary"
            not in str(error).lower()
        ):
            raise

        return _unir_unidades(
            oraciones,
            cantidad
        )

    relevancia = _calcular_relevancia(
        matriz_tfidf,
        titulo,
        vectorizador_resumen
    )

    seleccionados = _seleccionar_con_mmr(
        matriz_tfidf,
        relevancia,
        cantidad
    )

    elegidas = [
        oraciones[indice]
        for indice in sorted(
            seleccionados
        )
    ]

    return _unir_unidades(
        elegidas,
        cantidad
    )