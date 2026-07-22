from fastapi import FastAPI
from app.routes import contenido 

app = FastAPI(title="HoneyGuard API", version="1.0.0")

app.include_router(contenido.router)

@app.get("/health")
def health_check():
    return {"status": "ok"}