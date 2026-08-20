"""Pruebas de los esquemas Pydantic de app/schemas.py."""

import json
import warnings

import pytest
from pydantic import ValidationError

warnings.filterwarnings("ignore")


def test_respuesta_carga_exitosa_serializa_correctamente():
    from app.schemas import (
        RespuestaCargaExitosa,
        MetadatosResponse,
        ClasificacionResponse,
        DocumentoRelacionado,
        ContenidoResponse,
    )

    respuesta = RespuestaCargaExitosa(
        metadatos=MetadatosResponse(
            id=1,
            titulo="doc.pdf",
            autor="Juan",
            formato_archivo="pdf",
            tipo_contenido="articulo",
            url_archivo="https://x/y",
        ),
        clasificacion=ClasificacionResponse(
            categoria="DevOps",
            probabilidad=0.87,
            palabras_clave=["docker", "kubernetes"],
            resumen="Resumen de prueba.",
            requiere_revision=False,
        ),
        contenido_relacionado=[
            DocumentoRelacionado(id=2, titulo="otro.pdf", similitud=0.45)
        ],
        contenido=ContenidoResponse(texto_extraido="texto largo...", total_palabras=123),
    )

    # Debe poder serializarse a JSON real, no solo a dict de Python.
    payload = json.loads(respuesta.model_dump_json())
    assert payload["metadatos"]["id"] == 1
    assert payload["clasificacion"]["probabilidad"] == 0.87
    assert payload["contenido_relacionado"][0]["similitud"] == 0.45
    assert payload["contenido"]["total_palabras"] == 123


def test_respuesta_carga_exitosa_sin_documentos_relacionados():
    from app.schemas import (
        RespuestaCargaExitosa,
        MetadatosResponse,
        ClasificacionResponse,
        ContenidoResponse,
    )

    respuesta = RespuestaCargaExitosa(
        metadatos=MetadatosResponse(
            id=1, formato_archivo="txt", url_archivo="https://x"
        ),
        clasificacion=ClasificacionResponse(
            categoria="DevOps", probabilidad=0.5, requiere_revision=True
        ),
        contenido=ContenidoResponse(texto_extraido="texto", total_palabras=1),
    )
    assert respuesta.contenido_relacionado == []
    assert respuesta.clasificacion.palabras_clave == []


def test_respuesta_duplicado_serializa_correctamente():
    from app.schemas import RespuestaDuplicado, DocumentoOriginalDuplicado

    dup = RespuestaDuplicado(
        mensaje="El archivo ya existe en la base de conocimientos.",
        documento_original=DocumentoOriginalDuplicado(id=1, titulo="doc.pdf"),
        similitud=0.95,
    )
    payload = json.loads(dup.model_dump_json())
    assert payload["documento_original"]["id"] == 1
    assert payload["similitud"] == 0.95


def test_metadatos_response_requiere_campos_obligatorios():
    from app.schemas import MetadatosResponse

    with pytest.raises(ValidationError):
        # Falta 'id', 'formato_archivo' y 'url_archivo' (obligatorios).
        MetadatosResponse(titulo="doc.pdf")


def test_clasificacion_response_probabilidad_debe_ser_numerica():
    from app.schemas import ClasificacionResponse

    with pytest.raises(ValidationError):
        ClasificacionResponse(
            categoria="DevOps", probabilidad="no-es-numero", requiere_revision=False
        )
