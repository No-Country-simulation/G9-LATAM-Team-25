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

# Ruta absoluta a la carpeta del wallet
wallet_dir = Path(__file__).resolve().parent.parent / "wallet"

encoded_password = urllib.parse.quote_plus(DB_PASSWORD) if DB_PASSWORD else ""

# Alias definido exactamente en tu tnsnames.ora
DSN = "g9team25db_medium" 

DATABASE_URL = f"oracle+oracledb://{DB_USER}:{encoded_password}@{DSN}"

connect_args = {}
if wallet_dir.exists():
    wallet_path_str = str(wallet_dir.resolve())
    # config_dir carga tnsnames.ora y los certificados ssl del wallet automáticamente
    connect_args["config_dir"] = wallet_path_str
    connect_args["wallet_location"] = wallet_path_str

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