# Arquitectura de Infraestructura OCI - G9 Team 25

## 1. Servicios e Infraestructura Utilizados

* **API / Backend:** FastAPI desplegado de forma pública en Render PaaS (https://g9-latam-team-25.onrender.com).
* **Autonomous Database (ATP - g9team25db):** Base de datos relacional en Oracle Cloud Infrastructure (OCI) para la persistencia del análisis de contenidos (contenidos_procesados) y consultas del backend mediante conexión directa TLS (TCPS) con python-oracledb.
* **Object Storage (models-bucket):** Almacenamiento de artefactos de ML (modelo.pkl y vectorizer.pkl) accesibles vía solicitudes preautenticadas (PAR).
* **Resource Manager / Terraform:** Infraestructura como código para el aprovisionamiento de red (VCN, Subnet, Internet Gateway) y cómputo (Compute VM).

---

## 2. Diagrama de Conexión

               [ Usuario / Frontend ]
                         │
                         ▼
             [ API FastAPI en Render ]
          (g9-latam-team-25.onrender.com)
                         │
        ┌────────────────┼────────────────┐
        │ (Descarga PAR) │ (Persistencia) │
        ▼                ▼                ▼
[ Object Storage ] [ Modelo ML ] [ Autonomous DB ]
 (`models-bucket`)  (.pkl/.joblib) (`g9team25db`)

---

## 3. Descripción del Flujo

1. **Inicialización Backend:** La API FastAPI alojada en Render se conecta a OCI Object Storage mediante las URLs PAR para descargar en memoria el modelo y el vectorizador al arrancar el servicio.
2. **Procesamiento de Solicitudes:** La API procesa las peticiones enviadas por el usuario/frontend a través de endpoints HTTPS públicos.
3. **Persistencia en Nube:** Los resultados del análisis se insertan de manera segura en Oracle Autonomous Database en las tablas correspondientes (contenidos_procesados / ITEMS_PRUEBA).

---

## 4. Almacenamiento de Modelos — OCI Object Storage

* **Bucket Name:** models-bucket
* **Región:** Colombia Central (sa-bogota-1)
* **Archivos Almacenados:**
  * modelo.pkl: Modelo clasificador.
  * vectorizer.pkl: Vectorizador de texto.

### Variables de Entorno (.env)
* `MODEL_URL`: URL PAR para descargar el modelo.
* `VECTORIZER_URL`: URL PAR para descargar el vectorizador.
* `DB_USER` / `DB_PASSWORD`: Credenciales de acceso a Autonomous Database.

---

## 5. Configuración de Red, Conexión a Oracle DB y Lecciones Aprendidas

Para garantizar la conexión remota desde el entorno serverless de Render hacia OCI sin requerir archivos Wallet/mTLS locales ni drivers pesados, se ajustó la infraestructura de red en OCI:

* **Autenticación mTLS (Wallet):** Deshabilitada en la consola de OCI (Mutual TLS: Not required) para permitir conexiones seguras estándar mediante TLS directo (TCPS en el puerto 1522).
* **Access Control List (ACL):** Configurada para aceptar el bloque CIDR 0.0.0.0/0, permitiendo el tráfico entrante de las IPs dinámicas de Render.
* **Cadena de Conexión (SQLAlchemy + python-oracledb):** Se estructuró mediante el descriptor TCPS directo con security=(ssl_server_dn_match=yes) dentro de backend/app/database.py.

### Problemas Encontrados y Solución
* **Error DPY-6000 / DPY-6005 (Listener refused connection):**
  * *Causa:* La lista de control de acceso (ACL) de la base de datos en OCI estaba restringida a la IP local del desarrollador, bloqueando las peticiones enviadas por Render.
  * *Solución:* Se actualizó la ACL en OCI agregando la notación CIDR 0.0.0.0/0, permitiendo la sincronización y ejecución de consultas de la base de datos de manera fluida (200 OK).

---

## 6. Estado del Despliegue en Cómputo (Compute VM vs Render PaaS)

* **IaaS / Terraform:** La configuración de red e infraestructura as code fue probada y validada en el pipeline de OCI Resource Manager.
* **Estrategia de Despliegue Actual:** Debido a restricciones de capacidad temporal en las instancias Compute VM de la región (sa-bogota-1, error Out of host capacity), se adoptó Render PaaS para el hospedaje continuo de la API. Esto permite mantener el servicio disponible públicamente sin interrumpir la integración con Oracle Autonomous Database ni con OCI Object Storage.