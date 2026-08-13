# app/main.py
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ml_models.loader import load_model

ml_resources = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
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

app.include_router(contenido.router)