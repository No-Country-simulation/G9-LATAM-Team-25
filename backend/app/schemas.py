from pydantic import BaseModel, field_validator
from typing import Optional

class CargaContenidoRequest(BaseModel):
    # El título es opcional, por defecto es None
    titulo_documento: Optional[str] = None
    # El texto es estrictamente obligatorio
    texto_crudo: str

    @field_validator('texto_crudo')
    def texto_no_vacio(cls, value):
        # Validador personalizado: rechaza strings vacíos o puros espacios
        if not value or not value.strip():
            raise ValueError('El texto_crudo no puede estar vacío ni contener solo espacios en blanco.')
        return value