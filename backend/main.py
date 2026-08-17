import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.database import engine, Base
import app.models 
from app.routes import contenido, archivos 

# Crear tablas en Oracle Database
Base.metadata.create_all(bind=engine)

app = FastAPI(title="HoneyGuard API - Backend")

# --- Configuración de CORS completa para Lovable y entorno local ---
origins = [
    "http://localhost:5173",
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

# --- Registro de Routers ---
app.include_router(contenido.router)
app.include_router(archivos.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "database_user_configured": True}

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")