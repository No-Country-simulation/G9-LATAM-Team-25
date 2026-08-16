import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
import app.models 
from app.routes import contenido, archivos 

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Proyecto G9 Team 25 - Backend")

# Registro de routers de la API
app.include_router(contenido.router)
app.include_router(archivos.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "database_user_configured": True}

# Directorio absoluto hacia la compilación del frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.abspath(os.path.join(BASE_DIR, "..", "front-lovable", ".output", "public"))

if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return {"message": "Bienvenido a la API del Proyecto G9 Team 25"}