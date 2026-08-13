import re
import nltk
from nltk.corpus import stopwords

# Descargar el diccionario de palabras vacías (stopwords) la primera vez que arranque
try:
    stopwords.words('spanish')
except LookupError:
    nltk.download('stopwords', quiet=True)

stopwords_espanol = set(stopwords.words('spanish'))

def limpiar_texto(texto: str) -> str:
    """
    Replica la limpieza de texto realizada por Data Science para el modelo baseline.
    """
    texto = str(texto).lower()
    # Elimina números, símbolos y puntuación
    texto = re.sub(r'[^a-záéíóúñ\s]', ' ', texto)  
    palabras = texto.split()
    
    # Elimina palabras que no aportan significado (el, la, de, etc.)
    palabras_limpias = [p for p in palabras if p not in stopwords_espanol]
    
    return " ".join(palabras_limpias)