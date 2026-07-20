from fastapi import FastAPI
from app.database import engine, Base
import app.models  # Importante para que SQLAlchemy registre los modelos antes de crear las tablas

# Crea automáticamente las tablas definidas en models.py si aún no existen en Oracle
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Proyecto G9 Team 25 - Backend")

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API del Proyecto G9 Team 25"}

@app.get("/health")
def health_check():
    return {"status": "ok", "database_user_configured": True}