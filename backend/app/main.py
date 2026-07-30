# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
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

# --- AQUÍ ESTÁ LA CLAVE ---
# Asegúrate de que estas dos líneas estén sin el símbolo "#"
from app.routes import contenido
app.include_router(contenido.router)