
from dotenv import load_dotenv

import os
import nltk  # <-- NUEVO: Importación para descargar las stopwords de Data Science
from contextlib import asynccontextmanager

# Forzamos a Python a leer el archivo oculto .env
load_dotenv() 

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ml_models.loader import load_model




@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Asegurar que las stopwords estén descargadas en el servidor (Render)
    print("⏳ Descargando recursos de NLTK...")
    nltk.download('stopwords', quiet=True)
    print("✅ Stopwords listas.")

    # 2. Cargar tus modelos de IA y asignarlos al estado de la app
    modelo, vectorizador = load_model()
    if modelo and vectorizador:
        app.state.modelo = modelo
        app.state.vectorizador = vectorizador
        print("✅ Recursos de IA cargados en app.state.")
    else:
        print("⚠️ Advertencia: No se encontraron los modelos de IA.")

    yield

    # Opcional: Limpieza si fuera necesario, pero app.state se limpia automáticamente
    print("🛑 Servidor detenido.")


app = FastAPI(title="HoneyGuard API", lifespan=lifespan)

# --- CORS para Lovable ---
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
    # cubre cualquier subdominio de preview/publicación de Lovable
    allow_origin_regex=r"https://.*\.lovable\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
    max_age=86400,
)

# --- Routers (siempre después del middleware) ---
from app.routes import contenido

# Asegúrate de registrar el router para que FastAPI detecte tus endpoints.
# Si en tu archivo de rutas usas "router = APIRouter()", esta es la forma correcta:
app.include_router(contenido.router)