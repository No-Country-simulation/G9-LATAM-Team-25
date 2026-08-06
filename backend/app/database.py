import os
import urllib.parse
from pathlib import Path
import oracledb
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Ruta a la carpeta wallet
wallet_dir = Path(__file__).resolve().parent.parent / "wallet"

encoded_password = urllib.parse.quote_plus(DB_PASSWORD) if DB_PASSWORD else ""

DSN = "gee6aa642c1f765_g9team25db_medium"

DATABASE_URL = f"oracle+oracledb://{DB_USER}:{encoded_password}@{DSN}"

# En modo Thin, config_dir le indica a oracledb dónde buscar tnsnames.ora y wallet_location los certificados SSL
connect_args = {}
if wallet_dir.exists():
    connect_args["config_dir"] = str(wallet_dir)
    connect_args["wallet_location"] = str(wallet_dir)

engine = create_engine(
    DATABASE_URL, 
    connect_args=connect_args,
    echo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()