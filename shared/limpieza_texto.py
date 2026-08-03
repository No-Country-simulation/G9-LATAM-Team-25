"""Limpieza de texto común para entrenamiento e inferencia."""

from __future__ import annotations

import unicodedata
from collections.abc import Collection
from functools import lru_cache

from nltk.corpus import stopwords as nltk_stopwords


def _convertir_a_texto(texto: object | None) -> str:
    """Convierte entradas válidas a texto y representa ``None`` como vacío."""

    if texto is None:
        return ""
    if isinstance(texto, str):
        return texto
    return str(texto)


def normalizar_texto(texto: object | None) -> str:
    """Convierte a minúsculas, quita puntuación y normaliza espacios.

    La puntuación se reemplaza por espacios para evitar unir palabras separadas
    por guiones u otros signos. Se consideran todos los caracteres de
    puntuación Unicode, incluidos ``¿`` y ``¡``.
    """

    texto_normalizado = _convertir_a_texto(texto).lower()
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
