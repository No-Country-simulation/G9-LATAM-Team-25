# Arquitectura Preliminar OCI - G9 Team 25

> **Nota:** Este documento representa el diseño de arquitectura preliminar para el proyecto y está sujeto a cambios a medida que evolucione el desarrollo.

## 1. Servicios de Oracle Cloud Infrastructure (OCI) Utilizados

* **Autonomous Database (Transaction Processing - ATP):** Almacenamiento y gestión del dataset estructurado, información de usuarios y tablas relacionales del sistema.
* **Object Storage:** Almacenamiento de archivos no estructurados (documentos PDF, imágenes y archivos subidos por la aplicación).

## 2. Diagrama de Conexión

```text
[ Usuario / Frontend ]
           │
           ▼
    [ API (FastAPI) ]
           │
           ▼
  [ Modelo de Datos ]
           │
  ┌────────┴────────┐
  ▼                 ▼
[ Autonomous DB ]  [ Object Storage ]
 (Estructurado)      (Archivos)
```
## 3. Descripción del Flujo

1. **Usuario / Frontend:** Envía las peticiones hacia la API backend.
2. **API (FastAPI):** Maneja la lógica de negocio, validaciones y endpoints.
3. **Modelo / Servicios:** Procesa los datos y gestiona la comunicación hacia la infraestructura en la nube.
4. **OCI Infrastructure:**
   * **Autonomous DB:** Persiste y consulta la información relacional.
   * **Object Storage:** Guarda y entrega los objetos/archivos físicos.

## 📦 Almacenamiento de Modelos — OCI Object Storage

- **Bucket Name:** `models-bucket`
- **Región:** Colombia Central (Bogotá)
- **Archivos Almacenados:**
  - `modelo.pkl`: Modelo clasificador baseline.
  - `vectorizer.pkl`: Vectorizador de texto.

### Mecanismo de Acceso para Backend (FastAPI)
El Backend accederá a los archivos mediante **Pre-Authenticated Requests (PAR)** de lectura (o mediante el SDK de OCI `oci`), manteniendo las URLs seguras en las variables de entorno (`.env`):

- `MODEL_URL`: URL PAR para descargar `modelo.pkl`
- `VECTORIZER_URL`: URL PAR para descargar `vectorizer.pkl`