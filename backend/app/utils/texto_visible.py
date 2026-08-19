"""Extracción conservadora de texto visible desde contenido HTML.

La salida conserva mayúsculas, puntuación y términos tecnológicos para que
pueda usarse antes de procesos extractivos. Solo se retiran etiquetas HTML y
contenido no visible; no se aplican stopwords ni normalización léxica.
"""

from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser


__all__ = ["contiene_html_presentacion", "extraer_texto_visible"]


_ETIQUETAS_BLOQUE = frozenset(
    {
        "address",
        "article",
        "aside",
        "blockquote",
        "body",
        "br",
        "caption",
        "center",
        "datalist",
        "dd",
        "details",
        "desc",
        "dialog",
        "div",
        "dl",
        "dt",
        "fieldset",
        "figcaption",
        "figure",
        "footer",
        "form",
        "foreignobject",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "html",
        "legend",
        "li",
        "main",
        "menu",
        "nav",
        "ol",
        "optgroup",
        "option",
        "p",
        "pre",
        "section",
        "select",
        "summary",
        "svg",
        "table",
        "tbody",
        "td",
        "tfoot",
        "th",
        "thead",
        "textarea",
        "text",
        "textpath",
        "tr",
        "tspan",
        "ul",
    }
)
_ETIQUETAS_INLINE = frozenset(
    {
        "a",
        "abbr",
        "acronym",
        "area",
        "audio",
        "b",
        "base",
        "big",
        "bdi",
        "bdo",
        "button",
        "canvas",
        "circle",
        "clippath",
        "col",
        "colgroup",
        "cite",
        "code",
        "data",
        "del",
        "dfn",
        "defs",
        "em",
        "embed",
        "ellipse",
        "font",
        "filter",
        "g",
        "i",
        "iframe",
        "img",
        "input",
        "ins",
        "kbd",
        "label",
        "line",
        "lineargradient",
        "link",
        "map",
        "mark",
        "marker",
        "mask",
        "meta",
        "meter",
        "object",
        "o:p",
        "output",
        "param",
        "path",
        "pattern",
        "picture",
        "polygon",
        "polyline",
        "progress",
        "radialgradient",
        "rect",
        "q",
        "rp",
        "rt",
        "ruby",
        "s",
        "samp",
        "slot",
        "small",
        "source",
        "span",
        "strike",
        "strong",
        "stop",
        "sub",
        "sup",
        "symbol",
        "time",
        "track",
        "tt",
        "u",
        "use",
        "var",
        "video",
        "wbr",
    }
)
_ETIQUETAS_IGNORADAS = frozenset(
    {"head", "script", "style", "noscript", "template", "title"}
)
_ETIQUETAS_SALTO_SIMPLE = frozenset({"br"})
_ETIQUETAS_HTML_PRESENTACION = (
    _ETIQUETAS_BLOQUE | _ETIQUETAS_INLINE | _ETIQUETAS_IGNORADAS
)
_PATRON_HTML_PRESENTACION = re.compile(
    rf"</?(?:{'|'.join(sorted(map(re.escape, _ETIQUETAS_HTML_PRESENTACION)))})"
    r"(?=[\s/>])[^>]*>",
    flags=re.IGNORECASE,
)


class _ExtractorTextoVisible(HTMLParser):
    """Extrae contenido visible preservando estructura y signos adyacentes."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._partes: list[str] = []
        self._profundidad_ignorada = 0
        self._etiquetas_desconocidas_abiertas: list[str] = []

    def _agregar_salto(self, cantidad: int = 2) -> None:
        if not self._partes:
            return
        finales = len(self._partes[-1]) - len(self._partes[-1].rstrip("\n"))
        if finales < cantidad:
            self._partes.append("\n" * (cantidad - finales))

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        del attrs
        etiqueta = tag.casefold()
        if etiqueta in _ETIQUETAS_IGNORADAS:
            self._profundidad_ignorada += 1
            return
        if self._profundidad_ignorada:
            return
        if etiqueta in _ETIQUETAS_BLOQUE:
            self._agregar_salto(1 if etiqueta in _ETIQUETAS_SALTO_SIMPLE else 2)
        elif etiqueta not in _ETIQUETAS_INLINE:
            # Conserva genéricos tecnológicos como List<T> en texto plano.
            etiqueta_original = self.get_starttag_text()
            self._partes.append(etiqueta_original)
            coincidencia = re.match(r"<\s*([^\s/>]+)", etiqueta_original)
            if coincidencia:
                self._etiquetas_desconocidas_abiertas.append(coincidencia.group(1))

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        del attrs
        etiqueta = tag.casefold()
        if etiqueta in _ETIQUETAS_IGNORADAS:
            return
        if self._profundidad_ignorada:
            return
        if etiqueta in _ETIQUETAS_BLOQUE:
            self._agregar_salto(1 if etiqueta in _ETIQUETAS_SALTO_SIMPLE else 2)
        elif etiqueta not in _ETIQUETAS_INLINE:
            self._partes.append(self.get_starttag_text())

    def handle_endtag(self, tag: str) -> None:
        etiqueta = tag.casefold()
        if etiqueta in _ETIQUETAS_IGNORADAS:
            if self._profundidad_ignorada:
                self._profundidad_ignorada -= 1
            return
        if self._profundidad_ignorada:
            return
        if etiqueta in _ETIQUETAS_BLOQUE:
            self._agregar_salto(1 if etiqueta in _ETIQUETAS_SALTO_SIMPLE else 2)
        elif etiqueta not in _ETIQUETAS_INLINE:
            etiqueta_original = tag
            for indice in range(
                len(self._etiquetas_desconocidas_abiertas) - 1,
                -1,
                -1,
            ):
                candidata = self._etiquetas_desconocidas_abiertas[indice]
                if candidata.casefold() == etiqueta:
                    etiqueta_original = candidata
                    del self._etiquetas_desconocidas_abiertas[indice]
                    break
            self._partes.append(f"</{etiqueta_original}>")

    def handle_data(self, data: str) -> None:
        if not self._profundidad_ignorada:
            self._partes.append(data)

    def obtener_texto(self) -> str:
        contenido = "".join(self._partes).replace("\xa0", " ")
        contenido = re.sub(r"[ \t]+\n", "\n", contenido)
        contenido = re.sub(r"\n[ \t]+", "\n", contenido)
        contenido = re.sub(r"\n{3,}", "\n\n", contenido)
        return contenido.strip()


def extraer_texto_visible(texto: object | None) -> str:
    """Decodifica entidades y retira HTML sin alterar el contenido visible."""

    if texto is None:
        return ""
    contenido = texto if isinstance(texto, str) else str(texto)
    parser = _ExtractorTextoVisible()
    parser.feed(unescape(contenido))
    parser.close()
    return parser.obtener_texto()


def contiene_html_presentacion(texto: object | None) -> bool:
    """Indica si quedan etiquetas HTML conocidas en una cadena."""

    if texto is None:
        return False
    contenido = texto if isinstance(texto, str) else str(texto)
    return bool(_PATRON_HTML_PRESENTACION.search(contenido))
