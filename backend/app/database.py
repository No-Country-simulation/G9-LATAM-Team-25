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

# Descriptor completo del archivo tnsnames.ora
DSN = (
    "(description= "
    "(retry_count=20)(retry_delay=3)"
    "(address=(protocol=tcps)(port=1522)(host=adb.sa-bogota-1.oraclecloud.com))"
    "(connect_data=(service_name=gee6aa642c1f765_g9team25db_medium.adb.oraclecloud.com))"
    "(security=(ssl_server_dn_match=yes)))"
)

encoded_password = urllib.parse.quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
DATABASE_URL = f"oracle+oracledb://{DB_USER}:{encoded_password}@{DSN}"

# Ruta a la carpeta wallet
wallet_dir = Path(__file__).resolve().parent.parent / "wallet"

connect_args = {}
if wallet_dir.exists():
    # Se indica el directorio de configuración para los certificados
    connect_args["config_dir"] = str(wallet_dir.resolve())
    connect_args["wallet_location"] = str(wallet_dir.resolve())
    # Contraseña por defecto del wallet de Oracle mTLS si la requiere
    connect_args["wallet_password"] = ""

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