import io
import docx # Requiere: pip install python-docx
import PyPDF2 # Requiere: pip install PyPDF2
from fastapi import UploadFile

async def extraer_texto_plano(file: UploadFile) -> str:
    """
    Lee un archivo PDF, Word o TXT en memoria, extrae su texto plano 
    para la IA y regresa el archivo a su estado original para subirlo a OCI.
    """
    texto_extraido = ""
    # Obtenemos la extensión del archivo (pdf, docx, txt)
    extension = file.filename.split('.')[-1].lower()
    
    # 1. Leemos el archivo físico en bytes (en la memoria de FastAPI)
    contenido_bytes = await file.read()
    
    try:
        # 2. Extraemos el texto dependiendo del formato
        if extension == 'txt':
            texto_extraido = contenido_bytes.decode('utf-8')
            
        elif extension == 'pdf':
            # Simulamos el archivo en memoria para que PyPDF2 lo pueda leer
            lector_pdf = PyPDF2.PdfReader(io.BytesIO(contenido_bytes))
            for pagina in lector_pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto_extraido += texto_pagina + " "
                    
        elif extension in ['doc', 'docx']:
            # Simulamos el archivo en memoria para python-docx
            doc = docx.Document(io.BytesIO(contenido_bytes))
            texto_extraido = " ".join([parrafo.text for parrafo in doc.paragraphs])
            
        else:
            raise ValueError(f"El formato .{extension} no está soportado.")
            
    finally:
        # 3. 🚨 EL PASO MÁS IMPORTANTE 🚨
        # Regresamos el "cursor" del archivo a cero. Si no hacemos esto, 
        # cuando intentes subir el archivo a OCI, Oracle creerá que está vacío (0 bytes).
        await file.seek(0)
        
    return texto_extraido.strip()