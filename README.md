<p align="center"> <strong>Equipo tejONEs — Team 25</strong>

<br> Hackathon ONE · Alura + Oracle  </p>


<h1 align="center">Nombre del proyecto: HoneyGuard</h1>



## :triangular_ruler:

🛠 1.	Descripción del proyecto


El desafío asignado (TechMind — Organización Inteligente del Conocimiento Técnico) pide construir una solución que permita clasificar, organizar y facilitar la reutilización de contenido técnico (documentación, artículos, apuntes, tutoriales) usando técnicas de Ciencia de Datos, exponiendo los resultados vía una API REST integrada con OCI. 

Dividimos nuestra solución en dos niveles: el MVP obligatorio que pide el enunciado, y una funcionalidad diferenciadora que decidimos agregar sobre esa base. 
MVP obligatorio (lo mínimo que pide el enunciado) 

El hackathon pide, como requisito mínimo, un servicio que exponga al menos un endpoint capaz de recibir contenido técnico en texto plano y devolver información procesada. Concretamente: 
●	El usuario (o una aplicación cliente) envía un POST /contenido con {"titulo": "...", "texto": "..."}. 

●	Nuestro modelo de clasificación (entrenado con TF-IDF + Regresión Logística) procesa ese texto. La API devuelve {"categoria": "...", "probabilidad": ..., "informacion_adicional": [...]} con la categoría predicha, su probabilidad y palabras clave asociadas. 

Este es el flujo que se priorizará en el desarrollo del proyecto. Sobre esta base se implementará la funcionalidad diferenciadora descrita a continuación. 





## :triangular_ruler:


🛠 Nuestro enfoque / funcionalidad diferenciadora 

Sobre ese MVP, decidimos agregar una capa adicional pensada para un caso de uso real: que el usuario no siempre tenga el tiempo o los datos completos para catalogar su contenido a mano. 

●	El usuario podrá subir un archivo en formato .pdf o .txt (por el momento, estos son los únicos formatos soportados), en lugar de tener que copiar y pegar el texto a mano. 

●	El sistema lee el documento y extrae su contenido en texto plano, que se guarda en nuestro dataset propio. Esto nos permite acceder al contenido de forma más simple y entrenar el modelo con mayor facilidad. 

●	Si la persona que sube el archivo no completa todos los datos (por ejemplo, título, categoría o palabras clave), el modelo ya entrenado completa automáticamente los campos faltantes a partir del contenido del documento. En la interfaz de Lovable se muestran los campos autocompletados con un indicador visual de confianza, permitiendo a su vez al usuario poder editar y corregir esos campos antes de confirmar el guardado definitivo  — así se organiza mejor la base de conocimiento incluso con cargas incompletas.

●	Además, el usuario podrá buscar contenido y recibir como resultado los documentos ya
guardados que sean más parecidos a lo que busca (recomendación de contenidos relacionados por similitud de texto). 

●	Generación Automática de Resúmenes: Cuando se extraiga el texto plano del archivo, después de clasificado, se usa un enfoque extractivo sencillo para generar un resumen automático de 3 líneas del documento.

●	Clasificación automática de contenido: Cuando un usuario carga un documento o introduce texto manualmente, el sistema analiza su contenido y determina automáticamente la categoría a la que pertenece. 

El documento es convertido a texto plano - El texto es limpiado y preprocesado - Se genera una representación vectorial mediante TF-IDF - El modelo de Machine Learning predice la categoría más probable - La API devuelve la categoría junto con su nivel de confianza.

●	Detección de documentos similares: Antes de almacenar un nuevo documento, el sistema verifica si ya existe información muy parecida dentro de la base de conocimiento para evitar duplicados y ayuda a mantener organizada la información. Una vez vectorizado el documento, se compara con todos los documentos existentes mediante similitud coseno. Si la similitud supera un umbral determinado (por ejemplo, 90%), el sistema notifica al usuario que ya existe un documento muy similar. 

●	Generación automática de palabras clave: El sistema identifica los conceptos más importantes presentes en el documento para facilitar futuras búsquedas. Durante el procesamiento del texto se calcula la importancia de cada término mediante técnicas estadísticas (TF-IDF) y filtros lingüísticos, seleccionando únicamente las palabras con mayor relevancia. 




## :triangular_ruler:


🛠 ●	Para esto, la arquitectura contempla un almacenamiento híbrido: 

1.Oracle Autonomous Database: Aquí solo guardamos texto: el título, autor, palabras clave, la categoría que predice el programa

2.(OCI Object Storage): Aquí es donde se guardan físicamente los archivos .pdf o .txt que suben los usuarios.




## :triangular_ruler:


🛠 Delimitación de Áreas y Responsabilidades (Swimlanes / Carriles)

●	Usuario (Cliente / Operador): Interactúa con la interfaz web. Inicia las acciones (pegar texto, subir archivo, buscar) y consume las respuestas visuales.

●	Frontend (Lovable UI): Capa de presentación. Responsable de capturar la entrada del usuario, enviar peticiones HTTP/REST estructuradas al Backend y renderizar datos, indicadores de confianza y estados de error.

●	Backend (FastAPI - Orquestador Central): Es el único componente que interactúa con todas las demás áreas. Valida contratos Pydantic, maneja la lógica de negocio (umbrales, limpieza de archivos huérfanos), orquesta llamadas a Data Science y persiste/consulta en la nube de Oracle (OCI).

●	Data Science (Servicio de Inferencia ML/NLP): Encargado de la inteligencia del sistema. Expone funciones puras en Python para limpieza de texto, vectorización TF-IDF, clasificación con Regresión Logística, extracción de palabras clave, resúmenes extractivos y cálculo de similitud coseno. Nunca se comunica directamente con Frontend ni con la BD.

●	OCI Object Storage (Storage de Archivos Binarios): Repositorio no estructurado de Oracle Cloud. Almacena únicamente el archivo físico original.

●	OCI Autonomous Database (Base de Datos Relacional): Almacena metadatos, categoría, probabilidad, palabras clave, resumen, texto plano extraído y la URL de referencia de Object Storage.




## :triangular_ruler:


🛠 La arquitectura está diseñada bajo un enfoque desacoplado y modular de cuatro capas principales:

●	Capa de Cliente (Frontend): Desarrollada sobre Lovable, gestiona la interfaz gráfica de usuario para la carga de documentos, edición de metadatos y consultas de búsqueda.

●	Capa de Backend (FastAPI): Expone la API REST encargada de recibir las peticiones HTTP (POST para recepción de texto/archivos y búsquedas, y GET para consulta por ID). Cuenta con un Orquestador de Flujo que valida las solicitudes mediante esquemas Pydantic y garantiza el cumplimiento del contrato JSON.

●	Capa de Data Science (Inferencia): Módulo encargado del procesamiento de lenguaje natural (NLP) e inferencia analítica. Ejecuta el pipeline completo: extracción de texto (.pdf / .txt), limpieza y normalización, vectorización TF-IDF, clasificación mediante Regresión Logística, extracción de palabras clave, cálculo de Similitud Coseno y generación de resúmenes extractivos.

●	Capa de Persistencia (Oracle Cloud Infrastructure - OCI): Gestiona el almacenamiento híbrido dividiendo el archivo físico (Object Storage) de la información estructurada (Autonomous DB).




## :triangular_ruler:


🛠 Para optimizar el rendimiento y reducir el costo de almacenamiento en la base de datos, el sistema implementa una arquitectura de almacenamiento híbrido en Oracle Cloud Infrastructure (OCI):

●	OCI Object Storage: Actúa como el repositorio principal de binarios, almacenando únicamente los archivos planos o documentos originales (.pdf, .txt).

●	OCI Autonomous Database: Almacena la capa de datos relacional y los resultados del análisis analítico. Guarda metadatos como título, autor, categoría inferida, palabras clave, el texto extraído en formato plano para búsquedas y la URL de referencia generada por el Object Storage.

Esta separación permite mantener la base de datos liviana y altamente eficiente para consultas de texto e índices, sin sobrecargarla con el peso de archivos binarios.




## :triangular_ruler:


🛠 El contrato JSON estandariza la respuesta de la API REST hacia el cliente, agrupando la información procesada en cuatro objetos principales:

●	metadatos: Contiene los datos identificadores del archivo (id, titulo, autor, url_archivo, fecha_creacion).

●	clasificacion: Resumen analítico generado por el módulo de Data Science, incluyendo la categoria predecida, el nivel de probabilidad, un flag booleano requiere_revision (activado si la probabilidad es 0.70), lista de palabras_clave y el resumen sintético de 3 líneas.

●	contenido_relacionado: Lista de objetos con documentos similares hallados mediante métricas de distancia vectoriales (id, titulo, categoria, similitud).

●	contenido: Bloque que almacena el texto_extraido completo y el total_palabras. Nota de diseño: Este bloque utiliza una estrategia de Lazy Load; se omite en respuestas masivas o búsquedas para optimizar el consumo de ancho de banda y solo se envía al cliente cuando este consulta la vista detallada del registro (GET /contenido/{id}).
