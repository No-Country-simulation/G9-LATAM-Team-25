from fastapi import FastAPI
from app.database import engine, Base
import app.models  # SQLAlchemy registra los modelos
from app.routes import contenido, archivos  # Importas ambos módulos de rutas

# Crea automáticamente las tablas en Oracle DB si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Proyecto G9 Team 25 - Backend")

# Registro de routers
app.include_router(contenido.router)
app.include_router(archivos.router)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API del Proyecto G9 Team 25"}

@app.get("/health")
def health_check():
    return {"status": "ok", "database_user_configured": True}