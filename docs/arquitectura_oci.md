# Arquitectura de Infraestructura OCI - G9 Team 25

## 1. Servicios de Oracle Cloud Infrastructure (OCI) Utilizados

* **Autonomous Database (ATP - `g9team25db`):** Base de datos relacional para la persistencia del análisis de contenidos (`contenidos_procesados`) y consultas del backend mediante conexión `oracledb` con Instance Wallet.
* **Object Storage (`models-bucket`):** Almacenamiento de artefactos de ML (`modelo.pkl` y `vectorizer.pkl`) accesibles vía solicitudes preautenticadas (PAR).
* **Resource Manager / Terraform:** Infraestructura como código para el aprovisionamiento de red (`VCN`, `Subnet`, `Internet Gateway`) y cómputo (`Compute VM`).

## 2. Diagrama de Conexión

```text
               [ Usuario / Frontend ]
                         │
                         ▼
                  [ API (FastAPI) ]
                         │
        ┌────────────────┼────────────────┐
        │ (Descarga PAR) │ (Persistencia) │
        ▼                ▼                ▼
[ Object Storage ] [ Modelo ML ] [ Autonomous DB ]
 (`models-bucket`)  (.pkl/.joblib) (`g9team25db`)
```

## 3. Descripción del Flujo

1. **Inicialización Backend:** La API FastAPI se conecta a OCI Object Storage mediante las URLs PAR para descargar en memoria el modelo y el vectorizador.
2. **Procesamiento de Solicitudes:** La API procesa las peticiones enviadas por el usuario/frontend.
3. **Persistencia en Nube:** Los resultados del análisis se insertan de manera segura en Oracle Autonomous Database en la tabla `contenidos_procesados`.

## 4. Almacenamiento de Modelos — OCI Object Storage

* **Bucket Name:** `models-bucket`
* **Región:** Colombia Central (`sa-bogota-1`)
* **Archivos Almacenados:**
  * `modelo.pkl`: Modelo clasificador.
  * `vectorizer.pkl`: Vectorizador de texto.

### Variables de Entorno (`.env`)
* `MODEL_URL`: URL PAR para descargar el modelo.
* `VECTORIZER_URL`: URL PAR para descargar el vectorizador.
* `DB_USER` / `DB_PASSWORD`: Credenciales de acceso a Autonomous Database.

---

## 5. Estado del Despliegue en Cómputo (Compute VM)

* **IaaS / Terraform:** La configuración de red e infraestructura as code fue probada y validada en el pipeline de OCI Resource Manager.
* **Contingencia Regional:** El aprovisionamiento de la VM física se encuentra en pausa debido a restricciones de capacidad del proveedor en el Data Center de la región (`sa-bogota-1`, error `Out of host capacity`). La API ejecuta y conecta de forma transparente desde el entorno local hacia los servicios gestionados de OCI.