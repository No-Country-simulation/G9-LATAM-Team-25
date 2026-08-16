import joblib
import os
from pathlib import Path

def load_model():
    model = None
    vectorizer = None

    ml_models_dir = Path(__file__).resolve().parent
    backend_root_dir = ml_models_dir.parent.parent
    current_working_dir = Path(os.getcwd())

    search_paths = [ml_models_dir, backend_root_dir, current_working_dir]

    for base_dir in search_paths:
        model_path = base_dir / 'modelo.pkl'
        vectorizer_path = base_dir / 'vectorizer.pkl'
        
        print(f"🔍 Buscando modelos en: {base_dir}")

        if model_path.is_file() and vectorizer_path.is_file():
            print(f"✅ Archivos encontrados en {base_dir}. Intentando cargar...")
            try:
                model = joblib.load(model_path)
                vectorizer = joblib.load(vectorizer_path)
                print(f"🚀 ¡Modelo y vectorizador cargados exitosamente!")
                return model, vectorizer
            except Exception as e:
                print(f"❌ ERROR CRÍTICO al deserializar los .pkl: {e}")
        else:
            print(f"⏩ No están ambos archivos en {base_dir}")

    print("⚠️ Falló la carga en todas las rutas.")
    return None, None