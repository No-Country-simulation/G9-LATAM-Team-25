"""
Pruebas del módulo app/ml_models/loader.py.

Usa el modelo/vectorizador reales (modelo.pkl / vectorizer.pkl); no se
entrena ni modifica nada.
"""

import warnings

warnings.filterwarnings("ignore")


TEXTO_CORTO = (
    "Python es un lenguaje de programación utilizado para desarrollar "
    "aplicaciones web y sistemas de inteligencia artificial."
)

TEXTO_TECNICO = (
    "El uso de Docker y Kubernetes permite desplegar microservicios en "
    "contenedores. FastAPI junto con SQLAlchemy y Oracle permite construir "
    "APIs REST escalables usando Python y machine learning con scikit-learn."
)


# ============================================================
# Carga del modelo
# ============================================================

def test_load_model_carga_modelo_y_vectorizador():
    from app.ml_models.loader import load_model

    modelo, vectorizador = load_model()
    assert modelo is not None
    assert vectorizador is not None
    assert hasattr(modelo, "predict")
    assert hasattr(vectorizador, "transform")


# ============================================================
# Predicción de categoría
# ============================================================

def test_predecir_categoria_texto_valido():
    from app.ml_models.loader import predecir_categoria

    categoria, probabilidad, palabras_clave = predecir_categoria(
        TEXTO_CORTO, top_n_palabras_clave=8
    )
    assert categoria is not None
    assert isinstance(categoria, str)
    assert isinstance(probabilidad, float)
    assert 0.0 <= probabilidad <= 1.0
    assert isinstance(palabras_clave, list)
    assert len(palabras_clave) <= 8


def test_predecir_categoria_texto_tecnico():
    from app.ml_models.loader import predecir_categoria

    categoria, probabilidad, palabras_clave = predecir_categoria(
        TEXTO_TECNICO, top_n_palabras_clave=8
    )
    assert categoria is not None
    assert 0.0 <= probabilidad <= 1.0
    assert isinstance(palabras_clave, list)


def test_predecir_categoria_texto_vacio_no_lanza_excepcion():
    from app.ml_models.loader import predecir_categoria

    categoria, probabilidad, palabras_clave = predecir_categoria(
        "", top_n_palabras_clave=8
    )
    assert categoria is None
    assert probabilidad is None
    assert palabras_clave == []


def test_predecir_categoria_respeta_max_palabras_clave():
    from app.ml_models.loader import predecir_categoria

    _, _, palabras_clave = predecir_categoria(
        TEXTO_TECNICO, top_n_palabras_clave=3
    )
    assert len(palabras_clave) <= 3


# ============================================================
# Resumen
# ============================================================

def test_generar_resumen_texto_corto():
    from app.ml_models.loader import generar_resumen

    r = generar_resumen(
        "Python es un lenguaje de programación. Se usa para desarrollar aplicaciones web.",
        n_oraciones=3,
    )
    assert isinstance(r, str)
    assert len(r) > 0


def test_generar_resumen_texto_largo_respeta_n_oraciones():
    from app.ml_models.loader import generar_resumen, dividir_oraciones

    texto = " ".join(
        f"Esta es la oración número {i} sobre inteligencia artificial." for i in range(1, 30)
    )
    r = generar_resumen(texto, n_oraciones=3)
    assert len(dividir_oraciones(r)) <= 3


def test_generar_resumen_texto_vacio():
    from app.ml_models.loader import generar_resumen

    assert generar_resumen("", n_oraciones=3) == ""


def test_generar_resumen_varias_oraciones():
    from app.ml_models.loader import generar_resumen

    texto = (
        "La fotosíntesis es un proceso biológico. Ocurre en las plantas. "
        "Convierte luz en energía química. Es esencial para la vida en la Tierra. "
        "Produce oxígeno como subproducto."
    )
    r = generar_resumen(texto, n_oraciones=3)
    assert isinstance(r, str) and len(r) > 0


def test_generar_resumen_abreviaturas_no_corta_siglas():
    # Regresión del bug corregido: "(I.A.)." ya no debe partirse a
    # mitad de la sigla.
    from app.ml_models.loader import generar_resumen

    texto = (
        "El Dr. Pérez trabaja en EE. UU. desde hace 10 años. "
        "Su especialidad es la Inteligencia Artificial (I.A.). "
        "Publicó varios artículos, p. ej. sobre redes neuronales."
    )
    r = generar_resumen(texto, n_oraciones=3, titulo="Prueba")
    assert "(I.A.)" in r
    assert "(I." not in r.replace("(I.A.)", "")


# ============================================================
# Duplicados y similitud
# ============================================================

def test_chequear_duplicado_detecta_texto_identico():
    from app.ml_models.loader import chequear_duplicado

    doc_a = {
        "id": 1,
        "titulo": "Doc A",
        "texto": "Python es un lenguaje de programación utilizado para desarrollar aplicaciones.",
    }
    texto_b = "Python es un lenguaje de programación utilizado para desarrollar aplicaciones."

    es_duplicado, similitud, id_original, titulo_original = chequear_duplicado(
        texto_b, [doc_a], umbral=0.80
    )
    assert es_duplicado is True
    assert similitud >= 0.80
    assert id_original == 1
    assert titulo_original == "Doc A"


def test_chequear_duplicado_texto_distinto_no_es_duplicado():
    from app.ml_models.loader import chequear_duplicado

    doc_a = {
        "id": 1,
        "titulo": "Doc A",
        "texto": "Python es un lenguaje de programación utilizado para desarrollar aplicaciones.",
    }
    texto_c = (
        "La fotosíntesis es el proceso mediante el cual las plantas convierten "
        "energía luminosa en energía química."
    )

    es_duplicado, similitud, id_original, _ = chequear_duplicado(
        texto_c, [doc_a], umbral=0.80
    )
    assert es_duplicado is False
    assert id_original is None
    assert similitud < 0.80


def test_chequear_duplicado_documentos_db_vacio():
    from app.ml_models.loader import chequear_duplicado

    resultado = chequear_duplicado("cualquier texto", [], umbral=0.80)
    assert resultado == (False, 0.0, None, "")


def test_calcular_similitud_recomendaciones_documentos_db_vacio():
    from app.ml_models.loader import calcular_similitud_recomendaciones

    assert calcular_similitud_recomendaciones("texto", [], umbral=0.30) == []


def test_calcular_similitud_recomendaciones_no_incluye_umbral_bajo():
    from app.ml_models.loader import calcular_similitud_recomendaciones

    doc_a = {"id": 1, "texto": "Python es un lenguaje de programación."}
    doc_c = {
        "id": 2,
        "texto": "La fotosíntesis convierte energía luminosa en energía química.",
    }
    resultado = calcular_similitud_recomendaciones(
        "Python es un lenguaje de programación usado en la industria.",
        [doc_a, doc_c],
        umbral=0.30,
    )
    ids = [r[0] for r in resultado]
    assert 1 in ids
    assert 2 not in ids
