"""Resumen extractivo en español con TF-IDF, similitud coseno y MMR.

El módulo no descarga recursos ni carga modelos persistidos. Esto permite que
Data Science y Backend usen exactamente la misma función durante inferencia.
"""

from __future__ import annotations

import re
from math import ceil

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from shared.texto_visible import extraer_texto_visible


__all__ = ["dividir_oraciones", "generar_resumen"]


_PESO_RELEVANCIA_MMR = 0.65
_PESO_TITULO = 0.15
_MARCADOR_PUNTO = "\ue000"
_MARCADOR_ORACION = "\ue001"
_MAX_PALABRAS_UNIDAD = 35
_MAX_CARACTERES_UNIDAD = 320
_MAX_CARACTERES_DOCUMENTO_COMPLETO = 500

# Lista de NLTK para español incluida localmente. Evita que el servicio tenga
# que descargar el corpus ``stopwords`` durante el arranque o la inferencia.
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

_PATRON_EJEMPLO = re.compile(r"\bp\.\s*ej\.", flags=re.IGNORECASE)
_PATRONES_ABREVIATURAS_COMPUESTAS = (
    re.compile(r"\bee\.\s*uu\.", flags=re.IGNORECASE),
    re.compile(r"\b(?:a|d)\.\s*c\.", flags=re.IGNORECASE),
)
_PATRON_TRATAMIENTO = re.compile(
    r"\b(?:sr|sra|srta|dr|dra|ing|lic|prof|profa|ud|uds)\.",
    flags=re.IGNORECASE,
)
_PATRON_ABREVIATURA_CONTEXTO = re.compile(
    r"\b(?:etc|núm|nro|pág|págs|aprox|tel|vol|cap|art|arts)\.",
    flags=re.IGNORECASE,
)
_PATRON_INICIAL = re.compile(r"\b[A-ZÁÉÍÓÚÜÑ]\.(?=\s+[A-ZÁÉÍÓÚÜÑ])")
_PATRON_LIMITE = re.compile(
    r"(?P<puntuacion_cierre>[.!?]+)"
    r"(?P<cierres>['\"»”’)\]]+)"
    r"(?=\s+|$|\ue001|[¿¡«“‘A-ZÁÉÍÓÚÜÑ])"
    r"|(?P<puntuacion>[.!?]+)(?=\s+|$|\ue001|[¿¡'\"«“‘A-ZÁÉÍÓÚÜÑ])"
)
_PATRON_CPLUSPLUS = re.compile(r"(?<!\w)c\+\+(?!\w)", flags=re.IGNORECASE)
_PATRON_CSHARP = re.compile(r"(?<!\w)c#(?!\w)", flags=re.IGNORECASE)
_PATRON_DOTNET = re.compile(r"\.net\b", flags=re.IGNORECASE)
_PATRON_VINETA = re.compile(r"^(?:[-*•‣▪]|\d+[.)])\s+")
_INICIOS_ORACION_COMUNES = frozenset(
    """
    además ahora allí aunque así cuando después el ella ellas ellos en entonces
    esa esas ese esos esta estas este estos finalmente la las luego los mientras
    no nosotros por primero segundo sin también un una unas unos
    """.split()
)


def _validar_parametros(
    texto: str,
    n_oraciones: int,
    titulo: str | None,
) -> None:
    """Valida la API pública antes de procesar el documento."""

    if not isinstance(texto, str):
        raise TypeError("texto debe ser una cadena de caracteres")
    if isinstance(n_oraciones, bool) or not isinstance(n_oraciones, int):
        raise TypeError("n_oraciones debe ser un entero")
    if n_oraciones < 1:
        raise ValueError("n_oraciones debe ser mayor o igual que 1")
    if titulo is not None and not isinstance(titulo, str):
        raise TypeError("titulo debe ser una cadena de caracteres o None")


def _normalizar_espacios(texto: str) -> str:
    """Retira caracteres de control y compacta los espacios del documento."""

    sin_controles = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", " ", texto)
    return " ".join(sin_controles.split())


def _parece_lista_sin_marcadores(lineas: list[str]) -> bool:
    """Detecta listas breves escritas una entrada por línea."""

    return len(lineas) > 1 and all(
        len(linea.split()) <= 12
        and (linea[0].isupper() or linea[0].isdigit())
        and linea[-1] not in ",;:-"
        for linea in lineas
    )


def _normalizar_bloques(texto: str) -> list[str]:
    """Normaliza espacios conservando párrafos, viñetas y listas breves."""

    sin_marcadores = texto.replace(_MARCADOR_PUNTO, " ").replace(
        _MARCADOR_ORACION,
        " ",
    )
    sin_controles = re.sub(
        r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
        " ",
        sin_marcadores,
    )
    normalizado = sin_controles.replace("\r\n", "\n").replace("\r", "\n")
    # Algunos extractores concatenan encabezados o elementos de un temario
    # mediante tres o más espacios. Se conservan como límites estructurales.
    normalizado = re.sub(r"[ \t]{3,}", "\n\n", normalizado)
    grupos = re.split(r"\n\s*\n", normalizado)
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
                    bloques.append(" ".join(parrafo))
                    parrafo = []
                bloques.append(linea)
            else:
                parrafo.append(linea)
        if parrafo:
            bloques.append(" ".join(parrafo))

    return bloques


def _proteger_abreviatura_compuesta(coincidencia: re.Match[str]) -> str:
    """Protege puntos internos y evalúa si el punto final cierra oración."""

    abreviatura = coincidencia.group(0)
    partes = abreviatura.rsplit(".", maxsplit=1)
    internos = partes[0].replace(".", _MARCADOR_PUNTO)
    if len(partes) == 1:
        return internos

    resto = coincidencia.string[coincidencia.end() :]
    siguiente = re.search(r"\S+", resto)
    if siguiente is None:
        continua = False
    else:
        token = siguiente.group(0).strip("¿¡'\"«»“”‘’()[]{}.,;:").casefold()
        primer_caracter = siguiente.group(0)[0]
        continua = (
            primer_caracter.islower()
            or primer_caracter.isdigit()
            or primer_caracter in ",;:"
            or token not in _INICIOS_ORACION_COMUNES
        )
    punto_final = _MARCADOR_PUNTO if continua else "."
    return f"{internos}{punto_final}"


def _proteger_todos_los_puntos(coincidencia: re.Match[str]) -> str:
    """Protege todos los puntos de una abreviatura inequívoca."""

    return coincidencia.group(0).replace(".", _MARCADOR_PUNTO)


def _proteger_abreviatura_segun_contexto(
    coincidencia: re.Match[str],
) -> str:
    """Protege una abreviatura si continúa con minúscula, número o separador."""

    abreviatura = coincidencia.group(0)
    resto = coincidencia.string[coincidencia.end() :]
    siguiente = re.search(r"\S", resto)
    if siguiente is None:
        return abreviatura

    caracter = siguiente.group(0)
    if caracter.islower() or caracter.isdigit() or caracter in ",;:":
        return abreviatura.replace(".", _MARCADOR_PUNTO)
    return abreviatura


def _marcar_limite_oracion(coincidencia: re.Match[str]) -> str:
    """Inserta el límite distinguiendo comillas de apertura y de cierre."""

    puntuacion = (
        coincidencia.group("puntuacion_cierre")
        or coincidencia.group("puntuacion")
    )
    cierres = coincidencia.group("cierres") or ""
    siguiente = coincidencia.string[coincidencia.end() : coincidencia.end() + 1]

    if (
        cierres.startswith(('"', "'"))
        and siguiente
        and siguiente != _MARCADOR_ORACION
        and not siguiente.isspace()
    ):
        comilla = cierres[0]
        anteriores = coincidencia.string[: coincidencia.start()]
        posiciones = re.finditer(rf"(?<!\\){re.escape(comilla)}", anteriores)
        if comilla == "'":
            cantidad_abiertas = sum(
                not (
                    coincidencia.start() > 0
                    and coincidencia.end() < len(anteriores)
                    and anteriores[coincidencia.start() - 1].isalnum()
                    and anteriores[coincidencia.end()].isalnum()
                )
                for coincidencia in posiciones
            )
        else:
            cantidad_abiertas = sum(1 for _ in posiciones)
        if cantidad_abiertas % 2 == 0:
            return f"{puntuacion}{_MARCADOR_ORACION}{cierres}"

    return f"{puntuacion}{cierres}{_MARCADOR_ORACION}"


def _preprocesar_tfidf(texto: str) -> str:
    """Normaliza términos tecnológicos sin modificar la salida extractiva."""

    normalizado = texto.casefold()
    normalizado = _PATRON_CPLUSPLUS.sub(" cplusplus ", normalizado)
    normalizado = _PATRON_CSHARP.sub(" csharp ", normalizado)
    return _PATRON_DOTNET.sub(" dotnet ", normalizado)


def _fragmentar_unidad_larga(unidad: str) -> list[str]:
    """Divide bloques sobredimensionados sin inventar ni reescribir palabras.

    Es un fallback para índices, OCR o texto extraído sin puntuación. Los
    fragmentos se balancean para evitar una cola de una o dos palabras.
    """

    coincidencias = list(re.finditer(r"\S+", unidad))
    if not coincidencias:
        return []

    cantidad_fragmentos = max(
        ceil(len(coincidencias) / _MAX_PALABRAS_UNIDAD),
        ceil(len(unidad) / _MAX_CARACTERES_UNIDAD),
    )
    if cantidad_fragmentos <= 1:
        return [unidad]

    cantidad_fragmentos = min(cantidad_fragmentos, len(coincidencias))
    if cantidad_fragmentos <= 1:
        return [unidad]
    base, sobrantes = divmod(len(coincidencias), cantidad_fragmentos)
    fragmentos: list[str] = []
    inicio_palabra = 0
    for indice in range(cantidad_fragmentos):
        palabras_fragmento = base + (1 if indice < sobrantes else 0)
        fin_palabra = inicio_palabra + palabras_fragmento
        inicio_caracter = coincidencias[inicio_palabra].start()
        fin_caracter = coincidencias[fin_palabra - 1].end()
        fragmentos.append(unidad[inicio_caracter:fin_caracter].strip())
        inicio_palabra = fin_palabra

    # El reparto por palabras puede dejar un fragmento de código con tokens
    # mucho más largos que el promedio. Se vuelve a balancear hasta que cada
    # unidad sea estable al procesarse de forma aislada.
    resultado: list[str] = []
    for fragmento in fragmentos:
        subfragmentos = _fragmentar_unidad_larga(fragmento)
        if subfragmentos == [fragmento]:
            resultado.append(fragmento)
        else:
            resultado.extend(subfragmentos)
    return resultado


def _dividir_oraciones_base(
    texto: str,
    *,
    fragmentar_largos: bool,
) -> list[str]:
    """Segmenta una entrada, opcionalmente fragmentando bloques extensos."""

    bloques = _normalizar_bloques(texto)
    if not bloques:
        return []

    # Los saltos conservados por extractores de archivos suelen representar
    # párrafos, encabezados o elementos de lista sin puntuación final.
    bloques_protegidos = [
        re.sub(
            r"^(\d+)\.(?=\s)",
            lambda coincidencia: f"{coincidencia.group(1)}{_MARCADOR_PUNTO}",
            bloque,
        )
        for bloque in bloques
    ]
    texto_limpio = _MARCADOR_ORACION.join(bloques_protegidos)
    protegido = re.sub(
        r"(?<=\d)\.(?=\d)",
        _MARCADOR_PUNTO,
        texto_limpio,
    )
    protegido = _PATRON_EJEMPLO.sub(_proteger_todos_los_puntos, protegido)
    for patron in _PATRONES_ABREVIATURAS_COMPUESTAS:
        protegido = patron.sub(_proteger_abreviatura_compuesta, protegido)
    protegido = _PATRON_DOTNET.sub(
        lambda coincidencia: coincidencia.group(0).replace(
            ".",
            _MARCADOR_PUNTO,
            1,
        ),
        protegido,
    )
    protegido = _PATRON_TRATAMIENTO.sub(
        _proteger_abreviatura_compuesta,
        protegido,
    )
    protegido = _PATRON_ABREVIATURA_CONTEXTO.sub(
        _proteger_abreviatura_segun_contexto,
        protegido,
    )
    protegido = _PATRON_INICIAL.sub(
        _proteger_abreviatura_compuesta,
        protegido,
    )
    marcado = _PATRON_LIMITE.sub(_marcar_limite_oracion, protegido)

    oraciones: list[str] = []
    for fragmento in marcado.split(_MARCADOR_ORACION):
        restaurado = fragmento.replace(_MARCADOR_PUNTO, ".").strip()
        if restaurado:
            if fragmentar_largos:
                oraciones.extend(_fragmentar_unidad_larga(restaurado))
            else:
                oraciones.append(restaurado)
    return oraciones


def _dividir_texto_visible(texto_visible: str) -> list[str]:
    """Segmenta texto ya extraído sin volver a interpretar entidades o tags."""

    unidades = _dividir_oraciones_base(texto_visible, fragmentar_largos=True)
    for _ in range(4):
        estabilizadas: list[str] = []
        hubo_cambios = False
        for unidad in unidades:
            partes = _dividir_oraciones_base(
                unidad,
                fragmentar_largos=False,
            )
            if partes != [unidad]:
                hubo_cambios = True
            estabilizadas.extend(partes)
        unidades = estabilizadas
        if not hubo_cambios:
            break
    return unidades


def dividir_oraciones(texto: str) -> list[str]:
    """Divide texto español en unidades extractivas estables y sin descargas.

    Se protegen abreviaturas frecuentes, iniciales y números decimales antes
    de separar por punto, interrogación o exclamación. Las unidades conservan
    su redacción y puntuación. Una segunda pasada aislada evita que comillas o
    fragmentos de código cambien de segmentación al formar el resumen.
    """

    if not isinstance(texto, str):
        raise TypeError("texto debe ser una cadena de caracteres")

    return _dividir_texto_visible(extraer_texto_visible(texto))


def _eliminar_oraciones_duplicadas(oraciones: list[str]) -> list[str]:
    """Conserva la primera aparición de cada oración normalizada."""

    resultado: list[str] = []
    claves_vistas: set[str] = set()
    for oracion in oraciones:
        clave_lexica = " ".join(
            re.findall(r"\w+", _preprocesar_tfidf(oracion))
        )
        clave = clave_lexica or oracion.casefold().strip()
        if clave and clave not in claves_vistas:
            claves_vistas.add(clave)
            resultado.append(oracion)
    return resultado


def _calcular_relevancia(matriz_tfidf, titulo: str | None, vectorizador):
    """Puntúa cada oración contra el centroide y, si existe, el título."""

    centroide = matriz_tfidf.mean(axis=0).A
    relevancia = cosine_similarity(matriz_tfidf, centroide).ravel()

    titulo_limpio = _normalizar_espacios(extraer_texto_visible(titulo or ""))
    if titulo_limpio:
        vector_titulo = vectorizador.transform([titulo_limpio])
        if vector_titulo.nnz:
            similitud_titulo = cosine_similarity(
                matriz_tfidf,
                vector_titulo,
            ).ravel()
            relevancia = (
                (1.0 - _PESO_TITULO) * relevancia
                + _PESO_TITULO * similitud_titulo
            )

    return relevancia


def _seleccionar_con_mmr(matriz_tfidf, relevancia, cantidad: int) -> list[int]:
    """Selecciona índices relevantes penalizando contenido redundante."""

    candidatos = list(range(matriz_tfidf.shape[0]))
    primero = max(candidatos, key=lambda indice: (relevancia[indice], -indice))
    seleccionados = [primero]
    candidatos.remove(primero)

    while candidatos and len(seleccionados) < cantidad:
        similitudes = cosine_similarity(
            matriz_tfidf[candidatos],
            matriz_tfidf[seleccionados],
        ).max(axis=1)

        def clave(indice_local: int) -> tuple[float, float, int]:
            indice_oracion = candidatos[indice_local]
            puntuacion_mmr = (
                _PESO_RELEVANCIA_MMR * float(relevancia[indice_oracion])
                - (1.0 - _PESO_RELEVANCIA_MMR)
                * float(similitudes[indice_local])
            )
            return (
                puntuacion_mmr,
                float(relevancia[indice_oracion]),
                -indice_oracion,
            )

        mejor_local = max(range(len(candidatos)), key=clave)
        seleccionados.append(candidatos.pop(mejor_local))

    return seleccionados


def _unir_unidades(unidades: list[str], limite: int) -> str:
    """Une unidades sin crear límites nuevos ni exceder el máximo solicitado."""

    seleccionadas = unidades[:limite]
    como_parrafo = " ".join(seleccionadas)
    if _dividir_texto_visible(como_parrafo) == seleccionadas:
        return como_parrafo

    # Párrafos separados preservan viñetas, numeraciones y chunks sin signo
    # final cuando unirlos con un espacio cambiaría su segmentación.
    por_bloques = "\n\n".join(seleccionadas)
    if _dividir_texto_visible(por_bloques) == seleccionadas:
        return por_bloques

    # Resguardo defensivo ante una combinación de puntuación no contemplada.
    reparadas = _dividir_texto_visible(por_bloques)[:limite]
    return "\n\n".join(reparadas)


def generar_resumen(
    texto: str,
    n_oraciones: int = 3,
    *,
    titulo: str | None = None,
) -> str:
    """Genera un resumen extractivo de hasta ``n_oraciones``.

    Las oraciones se representan con TF-IDF y se puntúan por similitud coseno
    contra el centroide del documento. Si se proporciona ``titulo``, aporta un
    peso pequeño a la relevancia. MMR (Maximal Marginal Relevance) penaliza las
    selecciones similares. Finalmente, las oraciones elegidas se devuelven en
    el orden en que aparecían en el texto original.

    Un texto vacío devuelve ``""``. Un documento corto, de hasta 500
    caracteres visibles, se devuelve completo cuando no supera la cantidad
    solicitada; los documentos extensos y bloques sin puntuación se reducen.
    Cuando TF-IDF no encuentra vocabulario (por ejemplo, un texto formado solo
    por stopwords), se usa un fallback determinista con las primeras unidades.
    """

    _validar_parametros(texto, n_oraciones, titulo)
    texto_visible = extraer_texto_visible(texto)
    oraciones_originales = _dividir_texto_visible(texto_visible)
    if not oraciones_originales:
        return ""

    longitud_visible = len(_normalizar_espacios(texto_visible))
    if (
        len(oraciones_originales) <= n_oraciones
        and longitud_visible <= _MAX_CARACTERES_DOCUMENTO_COMPLETO
    ):
        return _unir_unidades(oraciones_originales, n_oraciones)

    oraciones = _eliminar_oraciones_duplicadas(oraciones_originales)
    cantidad = min(n_oraciones, len(oraciones))
    if (
        len(oraciones) <= n_oraciones
        and longitud_visible > _MAX_CARACTERES_DOCUMENTO_COMPLETO
        and cantidad > 1
    ):
        cantidad -= 1
    if len(oraciones) <= cantidad:
        return _unir_unidades(oraciones, cantidad)

    vectorizador = TfidfVectorizer(
        lowercase=False,
        preprocessor=_preprocesar_tfidf,
        stop_words=sorted(_STOPWORDS_ES),
        ngram_range=(1, 2),
        sublinear_tf=True,
        token_pattern=r"(?u)\b\w+\b",
    )
    try:
        matriz_tfidf = vectorizador.fit_transform(oraciones)
    except ValueError as error:
        if "empty vocabulary" not in str(error).lower():
            raise
        return _unir_unidades(oraciones, cantidad)

    relevancia = _calcular_relevancia(
        matriz_tfidf,
        titulo,
        vectorizador,
    )
    seleccionados = _seleccionar_con_mmr(
        matriz_tfidf,
        relevancia,
        cantidad,
    )
    elegidas = [oraciones[indice] for indice in sorted(seleccionados)]
    return _unir_unidades(elegidas, cantidad)
