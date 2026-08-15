[Diseño Técnico — Endpoint de Carga de Archivos (1).md](https://github.com/user-attachments/files/31095919/Diseno.Tecnico.Endpoint.de.Carga.de.Archivos.1.md)
# Diseño Técnico — Endpoint de Carga de Archivos

**Rama asignada:** `feat/back-carga-archivo`\
**Endpoint:** `POST /contenido/archivo`

## 1. Objetivo

El objetivo de este endpoint es coordinar el proceso completo de recepción y procesamiento de un nuevo documento.

El flujo contempla las siguientes etapas:

1. Validar el archivo recibido.
2. Almacenar el archivo en Oracle Cloud Infrastructure (OCI).
3. Extraer el texto del documento.
4. Verificar que el documento tenga contenido legible.
5. Comprobar si el documento ya existe en la base de conocimientos.
6. Procesar el contenido mediante los modelos de Inteligencia Artificial.
7. Guardar la información procesada en la base de datos.
8. Devolver al cliente la información correspondiente al documento creado.

El endpoint funcionará como el **orquestador principal del proceso**, coordinando las diferentes funciones de infraestructura, procesamiento de datos y persistencia.

---

# 2. Funciones necesarias

Para implementar correctamente el endpoint, se requiere disponer de las siguientes funciones. Cada área responsable debe revisar y confirmar el estado de las funciones asignadas.

## 2.1. Infraestructura — OCI

### `subir_archivo_oci(file)`

**Estado:** ⏳ Revisión / validación\
**Ubicación:** `app.utils.oci_storage`

**Responsabilidad:**

Recibir el archivo enviado por el usuario, autenticarse en Oracle Cloud Infrastructure y almacenarlo en el bucket destinado a documentos.

**Resultado esperado:**

Debe retornar un `string` que contenga la URL pública o la referencia segura del archivo almacenado.

---

### `borrar_archivo_oci(url_archivo)`

**Estado:** ⏳ Revisión / validación\
**Ubicación:** `app.utils.oci_storage`

**Responsabilidad:**

Eliminar de OCI un archivo que ya fue almacenado.

Esta función se utilizará principalmente como mecanismo de **rollback**, es decir, para limpiar el archivo cuando alguna etapa posterior del proceso falle.

**Resultado esperado:**

```text
True  → El archivo fue eliminado correctamente.
False → No fue posible eliminarlo.
```

Esta función es importante para evitar que queden archivos almacenados en OCI cuando el documento no pueda completar el proceso.

---

# 2.2. Data Science / NLP

### `limpiar_texto(texto)`

**Estado:** ✅ Disponible\
**Ubicación:** `app.utils.limpieza_de_texto`

**Responsabilidad:**

Preparar el texto para su procesamiento mediante:

- Conversión a minúsculas.
- Eliminación de caracteres especiales.
- Eliminación de *stopwords*.

---

### `extraer_texto_plano(file)`

**Estado:** ⏳ Pendiente de revisión por Data Science

**Responsabilidad:**

Abrir el archivo recibido, ya sea `.pdf` o `.txt`, y extraer su contenido en formato de texto.

**Regla de negocio:**

Si el documento:

- Es un PDF escaneado compuesto únicamente por imágenes.
- Está vacío.
- No contiene texto digital legible.

La función deberá detener el procesamiento mediante una excepción, por ejemplo `ValueError`, o devolver un texto vacío.

En cualquiera de estos casos, el endpoint deberá eliminar el archivo previamente almacenado en OCI y responder con un error `400 Bad Request`.

---

### `chequear_duplicado(texto_crudo, umbral=0.80)`

**Estado:** ⏳ Pendiente de revisión conjunta

**Responsabilidad:**

Determinar si el documento recibido es similar a alguno de los documentos existentes en la base de datos.

El proceso deberá:

1. Recibir el texto original.
2. Vectorizar el contenido.
3. Compararlo con los documentos existentes.
4. Calcular la similitud mediante similitud del coseno.
5. Determinar si la similitud supera el umbral establecido.

**Umbral inicial:**

```text
0.80
```

**Resultado esperado:**

La función deberá devolver información equivalente a:

```text
es_duplicado
similitud
titulo_original
```

Por ejemplo:

```python
(True, 0.87, "Reglamento Institucional")
```

---

### `predecir_categoria(texto_crudo)`

**Estado:** ✅ Disponible — Requiere mapeo

**Responsabilidad:**

Utilizar el modelo de Inteligencia Artificial cargado en memoria para determinar la categoría correspondiente al documento.

El resultado deberá proporcionar información como:

- Categoría.
- Probabilidad o nivel de confianza.
- Palabras clave o contenido relacionado.

**Consideración para Back-End:**

Los resultados provenientes de modelos de Machine Learning pueden contener tipos propios de NumPy.

Para evitar problemas de serialización con Pydantic o FastAPI, los valores deberán convertirse a tipos nativos de Python:

```python
str(categoria)
float(probabilidad)
```

---

### `generar_resumen(texto_crudo)`

**Estado:** ⏳ Pendiente de revisión por Data Science

**Responsabilidad:**

Generar automáticamente un resumen del contenido recibido.

El resumen deberá tener una extensión limitada, de acuerdo con la regla que se defina para el proyecto. Como referencia:

- Máximo 3 líneas, o
- Un número máximo definido de caracteres.

---

# 2.3. Base de Datos — CRUD

### `guardar_documento_db(...)`

**Estado:** ⏳ Pendiente de revisión / implementación

**Responsabilidad:**

Crear el registro definitivo del documento en la base de datos.

La información a almacenar deberá incluir, como mínimo:

- Título.
- Texto extraído.
- Categoría.
- Probabilidad.
- Palabras clave.
- Resumen.
- Autor.
- Tipo.
- URL del archivo almacenado en OCI.

La función deberá retornar el objeto correspondiente al registro creado para poder obtener su identificador generado por la base de datos.

---

# 3. Flujo general del endpoint

El endpoint seguirá un flujo secuencial. Cada etapa deberá completarse correctamente antes de pasar a la siguiente.

## Paso 1 — Validación del archivo

Se verifica que el archivo recibido tenga una extensión permitida:

```text
.pdf
.txt
```

Si el formato no es válido:

```text
HTTP 400 — Bad Request
```

Mensaje:

```text
Formato no soportado. Usa .pdf o .txt
```

---

## Paso 2 — Almacenamiento en OCI

Se ejecuta:

```python
subir_archivo_oci(file)
```

El archivo se almacena en OCI y se conserva temporalmente la URL obtenida.

La URL será necesaria tanto para guardar posteriormente el documento como para realizar un rollback en caso de error.

---

## Paso 3 — Extracción y validación del contenido

Se ejecuta:

```python
extraer_texto_plano(file)
```

Después se verifica que el resultado contenga texto.

Si el archivo está vacío o no contiene texto digital legible:

1. Se elimina el archivo de OCI.
2. Se cancela el procesamiento.
3. Se responde con `400 Bad Request`.

Esto evita almacenar archivos que no puedan ser procesados.

---

## Paso 4 — Detección de documentos duplicados

Se ejecuta:

```python
chequear_duplicado(texto_crudo, umbral=0.80)
```

Si el documento supera el umbral de similitud:

1. Se considera duplicado.
2. Se elimina el archivo de OCI.
3. No se crea ningún registro en la base de datos.
4. Se devuelve un mensaje informando que el documento ya existe.

La respuesta deberá incluir, cuando esté disponible:

- Porcentaje de similitud.
- Título del documento original.

---

## Paso 5 — Procesamiento mediante IA

Si el documento no es duplicado, se ejecutan las funciones de procesamiento:

```python
limpiar_texto(texto_crudo)
predecir_categoria(texto_crudo)
generar_resumen(texto_crudo)
```

Estas funciones permiten obtener la información necesaria para clasificar y describir el documento.

---

## Paso 6 — Persistencia

Una vez completado el procesamiento, se guarda la información en la base de datos mediante:

```python
guardar_documento_db(...)
```

El registro deberá almacenar tanto la información procesada como la referencia al archivo almacenado en OCI.

---

## Paso 7 — Respuesta

Si todo el proceso termina correctamente, el endpoint deberá devolver la información del documento creado utilizando el esquema Pydantic definido para el proyecto.

La respuesta deberá incluir, como mínimo:

```text
id
categoria
probabilidad
contenido_relacionado
autor
tipo
url_archivo
resumen
```

---

# 4. Manejo de errores y Rollback

El endpoint debe garantizar que no queden archivos innecesarios en OCI cuando el proceso falle.

La regla general será:

> **Si el archivo ya fue almacenado en OCI y posteriormente ocurre un error que impide completar el proceso, se deberá intentar eliminar el archivo mediante ****`borrar_archivo_oci()`****.**

### Casos principales

| Situación               | Acción                                     |
| ----------------------- | ------------------------------------------ |
| Formato inválido        | Responder `400`                            |
| Error al extraer texto  | Eliminar archivo de OCI y responder `400`  |
| Archivo vacío           | Eliminar archivo de OCI y responder `400`  |
| PDF escaneado sin texto | Eliminar archivo de OCI y responder `400`  |
| Documento duplicado     | Eliminar archivo de OCI y cancelar proceso |
| Error de IA             | Eliminar archivo de OCI y responder `500`  |
| Error de base de datos  | Eliminar archivo de OCI y responder `500`  |
| Error inesperado        | Intentar rollback y responder `500`        |

El rollback deberá ejecutarse siempre que `url_archivo` ya haya sido obtenida.

---

# 5. Implementación de referencia en FastAPI

La siguiente implementación representa la estructura esperada del endpoint:

```python
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status

# Importaciones de los módulos del proyecto:
# from app.utils.oci_storage import subir_archivo_oci, borrar_archivo_oci
# from app.utils.extraccion import extraer_texto_plano
# from app.ml_models.loader import (
#     chequear_duplicado,
#     predecir_categoria,
#     generar_resumen
# )
# from app.db.crud import guardar_documento_db

router = APIRouter()


@router.post("/contenido/archivo", status_code=status.HTTP_200_OK)
async def procesar_archivo(
    file: UploadFile = File(...),
    autor: str = Form(...),
    tipo: str = Form(...)
):
    # 1. Validar formato
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(
            status_code=400,
            detail="Formato no soportado. Usa .pdf o .txt"
        )

    url_archivo = None

    try:
        # 2. Almacenar archivo en OCI
        url_archivo = await subir_archivo_oci(file)

        # 3. Extraer texto
        try:
            texto_crudo = extraer_texto_plano(file)

            if not texto_crudo or len(texto_crudo.strip()) == 0:
                raise ValueError(
                    "El archivo no tiene texto digital legible."
                )

        except Exception as e:
            if url_archivo:
                await borrar_archivo_oci(url_archivo)

            raise HTTPException(
                status_code=400,
                detail=f"Error de extracción: {str(e)}"
            )

        # 4. Comprobar duplicados
        es_duplicado, similitud, titulo_orig = (
            chequear_duplicado(
                texto_crudo,
                umbral=0.80
            )
        )

        if es_duplicado:
            await borrar_archivo_oci(url_archivo)

            return {
                "mensaje": "Archivo existente en base de conocimientos.",
                "similitud": f"{similitud * 100:.2f}%",
                "titulo_original": titulo_orig
            }

        # 5. Procesamiento mediante IA
        categoria, probabilidad, palabras_clave = (
            predecir_categoria(texto_crudo)
        )

        resumen = generar_resumen(texto_crudo)

        # 6. Guardar en base de datos
        registro_db = guardar_documento_db(
            titulo=file.filename,
            texto=texto_crudo,
            categoria=categoria,
            probabilidad=probabilidad,
            palabras_clave=palabras_clave,
            resumen=resumen,
            autor=autor,
            tipo=tipo,
            url_archivo=url_archivo
        )

        # 7. Respuesta
        return {
            "id": registro_db.id,
            "categoria": str(categoria),
            "probabilidad": float(probabilidad),
            "contenido_relacionado": palabras_clave,
            "autor": autor,
            "tipo": tipo,
            "url_archivo": url_archivo,
            "resumen": resumen
        }

    except HTTPException:
        raise

    except Exception:
        # Rollback ante cualquier error inesperado
        if url_archivo:
            await borrar_archivo_oci(url_archivo)

        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )
```

---

# 6. Dependencias entre módulos

El endpoint depende de cuatro áreas principales:

```text
                    POST /contenido/archivo
                              │
                              ▼
                     ┌─────────────────┐
                     │ Validar archivo │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │      OCI        │
                     │ subir_archivo   │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ Extracción      │
                     │ de texto        │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ Duplicados      │
                     │ similitud ≥80% │
                     └────────┬────────┘
                              │
                         No duplicado
                              │
                              ▼
                     ┌─────────────────┐
                     │ Procesamiento   │
                     │ IA / NLP        │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │ Base de datos   │
                     │ guardar registro│
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │    Respuesta    │
                     └─────────────────┘
```

En caso de error después de almacenar el archivo, el flujo deberá regresar al módulo de OCI para ejecutar:

```python
borrar_archivo_oci(url_archivo)
```

---

# 7. Checklist de implementación

### Infraestructura — OCI

- [ ] Confirmar funcionamiento de `subir_archivo_oci(file)`.
- [ ] Confirmar que retorne correctamente la URL o referencia del archivo.
- [ ] Confirmar funcionamiento de `borrar_archivo_oci(url_archivo)`.
- [ ] Confirmar que el borrado pueda utilizarse como rollback.
- [ ] Verificar permisos de acceso al bucket.

### Data Science / NLP

- [x] Confirmar `limpiar_texto(texto)`.
- [ ] Revisar `extraer_texto_plano(file)`.
- [ ] Definir comportamiento para PDF escaneado.
- [ ] Definir comportamiento para archivos vacíos.
- [ ] Revisar `chequear_duplicado()`.
- [ ] Confirmar umbral de similitud de `0.80`.
- [x] Confirmar `predecir_categoria()`.
- [ ] Verificar conversión de resultados NumPy a tipos Python.
- [ ] Revisar `generar_resumen()`.
- [ ] Definir límite del resumen.

### Base de Datos

- [ ] Revisar `guardar_documento_db()`.
- [ ] Confirmar estructura de la tabla.
- [ ] Confirmar campos obligatorios.
- [ ] Confirmar generación del ID.
- [ ] Confirmar conexión con Oracle Autonomous Database o la BD utilizada en Render.

### Back-End

- [ ] Implementar `POST /contenido/archivo`.
- [ ] Validar extensiones permitidas.
- [ ] Integrar almacenamiento en OCI.
- [ ] Integrar extracción de texto.
- [ ] Integrar detección de duplicados.
- [ ] Integrar procesamiento de IA.
- [ ] Integrar persistencia en BD.
- [ ] Implementar rollback.
- [ ] Validar respuestas HTTP.
- [ ] Definir y aplicar el esquema Pydantic final.
- [ ] Probar flujo exitoso.
- [ ] Probar errores y rollback.

---

# 8. Resultado esperado

Al finalizar la implementación, el endpoint `POST /contenido/archivo` deberá ser capaz de recibir un documento y ejecutar automáticamente todo el proceso:

**Recepción → Validación → OCI → Extracción → Duplicados → IA → Base de datos → Respuesta**

El endpoint no deberá encargarse directamente de la lógica interna de cada módulo. Su responsabilidad principal será **coordinar cada componente, controlar el flujo y garantizar el manejo adecuado de errores y rollback**.

De esta manera, cada módulo mantiene una responsabilidad específica y el endpoint funciona como el punto central de integración entre **Back-End, OCI, Data Science/NLP y Base de Datos**.
