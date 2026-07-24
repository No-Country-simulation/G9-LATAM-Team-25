import os
from pathlib import Path
import oracledb
from dotenv import load_dotenv

# Fuerza a buscar el .env que está en la carpeta 'backend/'
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

dsn = (
    "(description=(retry_count=20)(retry_delay=3)"
    "(address=(protocol=tcps)(port=1522)(host=adb.sa-bogota-1.oraclecloud.com))"
    "(connect_data=(service_name=gee6aa642c1f765_g9team25db_medium.adb.oraclecloud.com))"
    "(security=(ssl_server_dn_match=yes)))"
)

print(f"Probando conexión para el usuario: '{user}'...")

try:
    connection = oracledb.connect(user=user, password=password, dsn=dsn)
    print("\n¡CONEXIÓN EXITOSA A ORACLE CLOUD!")
    connection.close()
except Exception as e:
    print(f"\nError de conexión de Oracle:\n{e}")