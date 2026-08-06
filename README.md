# 🚀 Integración del Modelo de IA y Validación de Entradas

## 📌 Rama: `feat/back-carga-modelo`
**Autor:** Carlos (Líder Backend / Full Stack - Equipo tejONEs)  
**Proyecto:** HoneyGuard - Hackathon ONE G9 (Alura + Oracle)

---

## 🎯 Objetivo de esta Rama
En esta etapa hemos transformado nuestra API de un prototipo con respuestas simuladas (mocks) a un **microservicio inteligente y completamente funcional**. La API ahora valida las entradas del usuario, limpia el texto con procesamiento de lenguaje natural (NLP) y ejecuta predicciones en tiempo real utilizando el modelo de Machine Learning entrenado por el equipo de Data Science.

---

## 🛠️ Modificaciones y Componentes Creados

### 1. 🛡️ Validación Estricta de Inputs (`app/schemas.py`)
- Definición de esquemas con **Pydantic**.
- `texto_crudo`: Campo **obligatorio**. Se añadió un validador personalizado que rechaza textos vacíos o compuestos únicamente por espacios en blanco, devolviendo un código **HTTP 422 Unprocessable Entity** con un mensaje claro.
- `titulo_documento`: Campo **opcional**.

### 2. 🧹 Módulo de Preprocesamiento NLP (`app/utils/limpieza_de_texto.py`)
- Creación de la función `limpiar_texto()` que replica con precisión la limpieza realizada durante el entrenamiento del modelo:
  - Conversión a minúsculas.
  - Eliminación de números, puntuación y caracteres especiales con expresiones regulares (`re`).
  - Remoción de *stopwords* en español mediante la librería `nltk`.

### 3. 🧠 Carga Eficiente de Modelos en Memoria (`app/main.py` & `app/ml_models/loader.py`)
- Implementación del ciclo de vida **`lifespan`** de FastAPI.
- Carga de los archivos serializados `modelo.pkl` y `vectorizer.pkl` usando `joblib` únicamente **una vez al arrancar el servidor**, manteniéndolos en memoria global. Esto garantiza respuestas inmediatas sin latencia por cada petición.

### 4. 🤖 Endpoint Predictivo Real (`app/routes/contenido.py`)
- Actualización de la ruta `POST /api/v1/contenido/cargar` (o `/contenido`).
- El flujo interno ejecuta:
  1. Recepción y validación del JSON de entrada.
  2. Limpieza del texto crudo.
  3. Vectorización TF-IDF con el vocabulario entrenado.
  4. Clasificación categórica (`modelo.predict`) y cálculo de la certidumbre/probabilidad matemática (`modelo.predict_proba`).
  5. Retorno del contrato JSON oficial (Categoría, Probabilidad, Título e Información adicional).

---

## ⚙️ Instrucciones para que el Equipo Pruebe esta Rama Localmente

### Pasos de Instalación:

1. **Clonar / Cambiar a la rama:**
   ```bash
   git checkout feat/back-carga-modelo
   git pull origin feat/back-carga-modelo
   ```

2. **Activar el entorno virtual e instalar dependencias:**
   ```bash
   # En Windows
   .\venv\Scripts\activate

   # Instalar librerías agregadas
   pip install fastapi uvicorn pydantic scikit-learn nltk joblib
   ```

3. **Verificar los archivos del modelo:**
   Asegúrate de contar con los archivos `modelo.pkl` y `vectorizer.pkl` en la siguiente ruta local (están ignorados en `.gitignore` por seguridad y peso):  
   `backend/app/ml_models/`

4. **Iniciar el servidor:**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Probar en Swagger UI:**
   - Navega a: `http://127.0.0.1:8000/docs`
   - Prueba el endpoint `POST` enviando un texto técnico real.

---

## 📊 Ejemplo de Petición y Respuesta

### Petición (Request Body):
```json
{
  "titulo_documento": "Manual de Arquitectura Cloud",
  "texto_crudo": "Docker es una plataforma que permite empaquetar una aplicación junto con todas sus dependencias en un contenedor. Kubernetes orquesta estos contenedores en la nube."
}
```

### Respuesta Exitosa (HTTP 200 OK):
```json
{
  "categoria": "Cloud",
  "probabilidad": 0.8543,
  "informacion_adicional": [],
  "titulo_recibido": "Manual de Arquitectura Cloud"
}
```

---

¡Listo para integración y revisión mediante Pull Request! 🚀
