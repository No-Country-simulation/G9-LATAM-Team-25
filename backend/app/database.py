import os
import urllib.parse
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carga el .env forzando el override de variables guardadas en memoria
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Codificar caracteres especiales como el * para SQLAlchemy
encoded_password = urllib.parse.quote_plus(DB_PASSWORD) if DB_PASSWORD else ""

DSN = (
    "(description=(retry_count=20)(retry_delay=3)"
    "(address=(protocol=tcps)(port=1522)(host=adb.sa-bogota-1.oraclecloud.com))"
    "(connect_data=(service_name=gee6aa642c1f765_g9team25db_medium.adb.oraclecloud.com))"
    "(security=(ssl_server_dn_match=yes)))"
)

DATABASE_URL = f"oracle+oracledb://{DB_USER}:{encoded_password}@{DSN}"

engine = create_engine(DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()