import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
import app.models  # SQLAlchemy registra los modelos
from app.routes import contenido, archivos  # Importas ambos módulos de rutas

# Crea automáticamente las tablas en Oracle DB si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Proyecto G9 Team 25 - Backend")

# Registro de routers de la API
app.include_router(contenido.router)
app.include_router(archivos.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "database_user_configured": True}

# Configuración para servir la interfaz estática compilada de React/Vite
frontend_path = os.path.join(os.path.dirname(__file__), "..", "front-lovable", ".output", "public")

if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return {"message": "Bienvenido a la API del Proyecto G9 Team 25"}