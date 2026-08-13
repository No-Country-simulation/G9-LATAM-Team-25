# app/ml_models/loader.py
import joblib
import os
import logging

logger = logging.getLogger(__name__)

# Rutas absolutas para evitar errores de directorio
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'modelo.pkl')
VECTORIZER_PATH = os.path.join(BASE_DIR, 'vectorizer.pkl')

def load_model():
    try:
        modelo = joblib.load(MODEL_PATH)
        vectorizador = joblib.load(VECTORIZER_PATH)
        logger.info("Modelo y vectorizador cargados exitosamente.")
        return modelo, vectorizador
    except FileNotFoundError as e:
        logger.error(f"Error cargando los modelos: {e}. Asegúrate de que los archivos .pkl existan.")
        return None, None