"""
Pruebas del endpoint POST /contenido/archivo.

OCI y Oracle real no están disponibles en este entorno, así que:
- Oracle se sustituye por SQLite en memoria (ver conftest.py).
- OCI se mockea directamente sobre las funciones importadas en
  app.routes.contenido (subir_archivo_oci / borrar_archivo_oci),
  para no depender de credenciales ni red hacia OCI.
"""

import io
import warnings

import pytest

warnings.filterwarnings("ignore")


def _archivo_txt(nombre="documento.txt", contenido=b"Contenido de prueba valido."):
    return {"file": (nombre, io.BytesIO(contenido), "text/plain")}


def _form_valido():
    return {"autor": "Autor de Prueba", "tipo": "articulo"}


# ============================================================
# Escenario 1 - Éxito
# ============================================================

def test_escenario_1_exito(client, monkeypatch):
    import app.routes.contenido as contenido_mod

    async def fake_subir(file):
        return "https://objectstorage.fake-region.oraclecloud.com/n/ns/b/bucket/o/fake-uuid.txt"

    async def fake_borrar(url):
        return True

    monkeypatch.setattr(contenido_mod, "subir_archivo_oci", fake_subir)
    monkeypatch.setattr(contenido_mod, "borrar_archivo_oci", fake_borrar)

    resp = client.post(
        "/contenido/archivo",
        files=_archivo_txt(
            contenido=(
                b"Python es un lenguaje de programacion utilizado para "
                b"desarrollar aplicaciones web y sistemas de inteligencia "
                b"artificial. Se utiliza junto con FastAPI y SQLAlchemy."
            )
        ),
        data=_form_valido(),
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "metadatos" in data and "clasificacion" in data
    assert "contenido_relacionado" in data and "contenido" in data
    assert data["metadatos"]["id"] is not None
    assert isinstance(data["clasificacion"]["probabilidad"], float)
    assert 0 <= data["clasificacion"]["probabilidad"] <= 1
    assert isinstance(data["clasificacion"]["palabras_clave"], list)


# ============================================================
# Escenario 2 - Archivo con formato inválido
# ============================================================

@pytest.mark.parametrize("nombre", ["malware.exe", "foto.jpg", "documento.doc"])
def test_escenario_2_formato_invalido(client, monkeypatch, nombre):
    import app.routes.contenido as contenido_mod

    async def fake_subir(file):
        raise AssertionError("No debe llamarse a OCI si el formato es invalido")

    monkeypatch.setattr(contenido_mod, "subir_archivo_oci", fake_subir)

    resp = client.post(
        "/contenido/archivo",
        files={"file": (nombre, io.BytesIO(b"contenido"), "application/octet-stream")},
        data=_form_valido(),
    )

    assert 400 <= resp.status_code < 500, resp.text


# ============================================================
# Escenario 3 - Archivo vacío
# ============================================================

def test_escenario_3_archivo_vacio(client, monkeypatch):
    import app.routes.contenido as contenido_mod

    async def fake_subir(file):
        return "https://objectstorage.fake/n/ns/b/bucket/o/vacio.txt"

    borrado = {"llamado": False}

    async def fake_borrar(url):
        borrado["llamado"] = True
        return True

    monkeypatch.setattr(contenido_mod, "subir_archivo_oci", fake_subir)
    monkeypatch.setattr(contenido_mod, "borrar_archivo_oci", fake_borrar)

    resp = client.post(
        "/contenido/archivo",
        files=_archivo_txt(contenido=b""),
        data=_form_valido(),
    )

    assert 400 <= resp.status_code < 500, resp.text
    assert borrado["llamado"] is True


# ============================================================
# Escenario 4 - Documento duplicado
# ============================================================

def test_escenario_4_duplicado(client, monkeypatch):
    import app.routes.contenido as contenido_mod

    async def fake_subir(file):
        return "https://objectstorage.fake/n/ns/b/bucket/o/dup.txt"

    borrado = {"llamado": False, "url": None}

    async def fake_borrar(url):
        borrado["llamado"] = True
        borrado["url"] = url
        return True

    def fake_chequear_duplicado(texto, documentos_existentes, umbral):
        return True, 0.95, 1, "original.txt"

    llamado_crear_documento = {"llamado": False}
    crear_original = contenido_mod.crear_documento

    def spy_crear_documento(*args, **kwargs):
        llamado_crear_documento["llamado"] = True
        return crear_original(*args, **kwargs)

    monkeypatch.setattr(contenido_mod, "subir_archivo_oci", fake_subir)
    monkeypatch.setattr(contenido_mod, "borrar_archivo_oci", fake_borrar)
    monkeypatch.setattr(contenido_mod, "chequear_duplicado", fake_chequear_duplicado)
    monkeypatch.setattr(contenido_mod, "crear_documento", spy_crear_documento)

    resp = client.post(
        "/contenido/archivo",
        files=_archivo_txt(),
        data=_form_valido(),
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["mensaje"] == "El archivo ya existe en la base de conocimientos."
    assert data["documento_original"]["id"] == 1
    assert data["similitud"] == 0.95

    assert llamado_crear_documento["llamado"] is False
    assert borrado["llamado"] is True


# ============================================================
# Escenario 5 - Error de ML (predecir_categoria lanza excepción)
# ============================================================

def test_escenario_5_error_ml(client, monkeypatch):
    import app.routes.contenido as contenido_mod

    async def fake_subir(file):
        return "https://objectstorage.fake/n/ns/b/bucket/o/mlerror.txt"

    borrado = {"llamado": False}

    async def fake_borrar(url):
        borrado["llamado"] = True
        return True

    def fake_predecir_categoria(texto, top_n_palabras_clave):
        raise RuntimeError("Fallo simulado del modelo de clasificacion")

    llamado_crear_documento = {"llamado": False}
    crear_original = contenido_mod.crear_documento

    def spy_crear_documento(*args, **kwargs):
        llamado_crear_documento["llamado"] = True
        return crear_original(*args, **kwargs)

    monkeypatch.setattr(contenido_mod, "subir_archivo_oci", fake_subir)
    monkeypatch.setattr(contenido_mod, "borrar_archivo_oci", fake_borrar)
    monkeypatch.setattr(contenido_mod, "predecir_categoria", fake_predecir_categoria)
    monkeypatch.setattr(contenido_mod, "crear_documento", spy_crear_documento)

    resp = client.post(
        "/contenido/archivo",
        files=_archivo_txt(),
        data=_form_valido(),
    )

    assert resp.status_code == 500, resp.text
    assert borrado["llamado"] is True
    assert llamado_crear_documento["llamado"] is False


# ============================================================
# Escenario 6 - Error de BD (crear_documento falla)
# ============================================================

def test_escenario_6_error_bd(client, monkeypatch):
    import app.routes.contenido as contenido_mod

    async def fake_subir(file):
        return "https://objectstorage.fake/n/ns/b/bucket/o/dberror.txt"

    borrado = {"llamado": False}

    async def fake_borrar(url):
        borrado["llamado"] = True
        return True

    def fake_crear_documento(*args, **kwargs):
        raise RuntimeError("Fallo simulado al guardar en Oracle")

    monkeypatch.setattr(contenido_mod, "subir_archivo_oci", fake_subir)
    monkeypatch.setattr(contenido_mod, "borrar_archivo_oci", fake_borrar)
    monkeypatch.setattr(contenido_mod, "crear_documento", fake_crear_documento)

    resp = client.post(
        "/contenido/archivo",
        files=_archivo_txt(),
        data=_form_valido(),
    )

    assert resp.status_code == 500, resp.text
    data = resp.json()
    assert "detail" in data
    assert borrado["llamado"] is True
