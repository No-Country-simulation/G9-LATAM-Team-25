import os
import nltk
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# 1. Cargar variables de entorno forzando la ruta (Para Oracle y CORS)
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importaciones locales de tu proyecto
from app.ml_models.loader import load_model
from app.database import engine, Base
import app.models  # Obligatorio para que SQLAlchemy registre los modelos
from app.routes import contenido

# 2. Crea automáticamente las tablas en Oracle si aún no existen[cite: 6]
Base.metadata.create_all(bind=engine)

ml_resources = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 3. Descargar NLTK para Data Science (Render)
    print("⏳ Descargando recursos de NLTK...")
    nltk.download('stopwords', quiet=True)
    print("✅ Stopwords listas.")

    # 4. Cargar Modelos de IA en memoria[cite: 10]
    modelo, vectorizador = load_model()
    if modelo and vectorizador:
        ml_resources["modelo"] = modelo
        ml_resources["vectorizador"] = vectorizador
        print("✅ Recursos de IA cargados en memoria.")
    else:
        print("⚠️ Advertencia: No se encontraron los modelos de IA.")

    yield
    ml_resources.clear()
    print("🛑 Recursos de IA liberados.")


# 5. Inicializar la app de FastAPI de forma unificada[cite: 10]
app = FastAPI(title="HoneyGuard API", lifespan=lifespan)

# 6. Configurar CORS para Lovable[cite: 10]
origins = [
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "https://honeyguard-organizer.lovable.app",
    "https://id-preview--f783ecb1-2818-4c4b-8c76-abd07625c703.lovable.app",
]

extra = os.getenv("CORS_EXTRA_ORIGINS", "")
origins += [o.strip() for o in extra.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.lovable\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
    max_age=86400,
)

# 7. Registrar tu archivo de rutas[cite: 10]
app.include_router(contenido.router)

# 8. Endpoints base[cite: 6]
@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API de HoneyGuard - Proyecto G9 Team 25"}

@app.get("/health")
def health_check():
    return {"status": "ok", "database_user_configured": True}