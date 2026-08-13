"""Limpieza de texto común para entrenamiento e inferencia."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Collection
from functools import lru_cache
from html import unescape
from html.parser import HTMLParser

from nltk.corpus import stopwords as nltk_stopwords


_PATRON_URL = re.compile(
    r"\b(?:https?://|www\.)\S+"
    r"|\b(?:[a-z0-9-]+\.)+[a-z]{2,}/\S+",
    flags=re.IGNORECASE,
)


def _convertir_a_texto(texto: object | None) -> str:
    """Convierte entradas válidas a texto y representa ``None`` como vacío."""

    if texto is None:
        return ""
    if isinstance(texto, str):
        return texto
    return str(texto)


class _ExtractorTextoHTML(HTMLParser):
    """Extrae texto visible y descarta etiquetas, scripts y estilos."""

    _ETIQUETAS_IGNORADAS = frozenset({"script", "style"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._partes: list[str] = []
        self._profundidad_ignorada = 0

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        """Ignora el contenido que no representa texto visible."""

        del attrs
        if tag.casefold() in self._ETIQUETAS_IGNORADAS:
            self._profundidad_ignorada += 1

    def handle_endtag(self, tag: str) -> None:
        """Finaliza una sección de contenido ignorado."""

        if (
            tag.casefold() in self._ETIQUETAS_IGNORADAS
            and self._profundidad_ignorada
        ):
            self._profundidad_ignorada -= 1

    def handle_data(self, data: str) -> None:
        """Conserva únicamente el texto visible del documento."""

        if not self._profundidad_ignorada:
            self._partes.append(data)

    def obtener_texto(self) -> str:
        """Devuelve los fragmentos visibles separados por espacios."""

        return " ".join(self._partes)


def _extraer_texto_html(texto: object | None) -> str:
    """Decodifica entidades HTML y retira etiquetas del contenido."""

    contenido_decodificado = unescape(_convertir_a_texto(texto))
    parser = _ExtractorTextoHTML()
    parser.feed(contenido_decodificado)
    parser.close()
    return parser.obtener_texto()


def normalizar_texto(texto: object | None) -> str:
    """Quita URLs, convierte a minúsculas y normaliza puntuación y espacios.

    La puntuación se reemplaza por espacios para evitar unir palabras separadas
    por guiones u otros signos. Se consideran todos los caracteres de
    puntuación Unicode, incluidos ``¿`` y ``¡``.
    """

    texto_sin_urls = _PATRON_URL.sub(" ", _extraer_texto_html(texto))
    texto_normalizado = texto_sin_urls.lower()
    sin_puntuacion = "".join(
        " " if unicodedata.category(caracter).startswith("P") else caracter
        for caracter in texto_normalizado
    )
    return " ".join(sin_puntuacion.split())


@lru_cache(maxsize=1)
def obtener_stopwords_espanol() -> frozenset[str]:
    """Devuelve las stopwords españolas de NLTK, almacenadas en memoria."""

    try:
        return frozenset(palabra.casefold() for palabra in nltk_stopwords.words("spanish"))
    except LookupError as error:
        mensaje = (
            "No se encontró el corpus 'stopwords' de NLTK. "
            "Instálalo una vez con: python -m nltk.downloader stopwords"
        )
        raise LookupError(mensaje) from error


def quitar_stopwords(
    texto: object | None,
    palabras_vacias: Collection[str] | None = None,
) -> str:
    """Elimina palabras completas incluidas en el vocabulario de stopwords."""

    contenido = _convertir_a_texto(texto)
    if palabras_vacias is None:
        vocabulario_normalizado = obtener_stopwords_espanol()
    else:
        vocabulario_normalizado = {
            palabra.casefold() for palabra in palabras_vacias
        }
    return " ".join(
        palabra
        for palabra in contenido.split()
        if palabra.casefold() not in vocabulario_normalizado
    )


def limpiar_texto(
    texto: object | None,
    palabras_vacias: Collection[str] | None = None,
) -> str:
    """Normaliza un texto y elimina stopwords en español.

    ``palabras_vacias`` permite inyectar un vocabulario alternativo en pruebas
    o casos de negocio específicos. Si se omite, se usa el corpus de NLTK.
    """

    return quitar_stopwords(normalizar_texto(texto), palabras_vacias)