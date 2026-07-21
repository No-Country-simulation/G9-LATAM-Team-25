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