import os
from pathlib import Path
import oracledb
from dotenv import load_dotenv

# Cargar variables del .env
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

# DSN usando el Wallet (o tu cadena DSN previa)
WALLET_DIR = os.path.abspath("./wallet")
dsn = "g9team25db_high"

print(f"Probando conexión a OCI para el usuario: '{user}'...")

try:
    connection = oracledb.connect(
        user=user,
        password=password,
        dsn=dsn,
        config_dir=WALLET_DIR,
        wallet_location=WALLET_DIR,
        wallet_password=password
    )
    print("✅ ¡CONEXIÓN EXITOSA A ORACLE CLOUD!")

    cursor = connection.cursor()

    # Probar operaciones básicas
    cursor.execute("SELECT id, titulo, categoria FROM contenidos_procesados ORDER BY id DESC")
    registro = cursor.fetchone()
    print(f"📖 Último registro en BD: {registro}")

    cursor.close()
    connection.close()

except Exception as e:
    print(f"❌ Error de conexión de Oracle:\n{e}")