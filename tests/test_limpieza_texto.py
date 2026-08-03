"""Pruebas del procesamiento compartido de texto.

Finalidad:
    Verificar que Data Science y Backend obtengan exactamente el mismo texto
    limpio y detectar regresiones si la implementación cambia en el futuro.

Ejecución desde la raíz del repositorio:
    python -m unittest discover -s tests -v

Las pruebas inyectan vocabularios pequeños de stopwords cuando corresponde.
Así comprueban cada regla de forma determinista y no dependen del contenido
completo del corpus durante la prueba unitaria.
"""

import unittest

from shared.limpieza_texto import (
    limpiar_texto,
    normalizar_texto,
    quitar_stopwords,
)


class LimpiezaTextoTests(unittest.TestCase):
    """Valida las reglas públicas que forman el contrato de limpieza."""

    def test_normaliza_minusculas_puntuacion_unicode_y_espacios(self) -> None:
        """Comprueba minúsculas, puntuación Unicode y espacios sobrantes."""

        resultado = normalizar_texto("  ¡Hola, MUNDO! Python—Backend...  ")
        self.assertEqual(resultado, "hola mundo python backend")

    def test_quita_stopwords_como_palabras_completas(self) -> None:
        """Comprueba que solo se retiren stopwords completas del vocabulario."""

        resultado = quitar_stopwords(
            "el desarrollo del backend elegante",
            palabras_vacias={"el", "del", "de"},
        )
        self.assertEqual(resultado, "desarrollo backend elegante")

    def test_limpieza_unifica_los_dos_pasos(self) -> None:
        """Comprueba que limpiar_texto combine normalización y stopwords."""

        resultado = limpiar_texto(
            "¡Curso DE Python para principiantes!",
            palabras_vacias={"de", "para"},
        )
        self.assertEqual(resultado, "curso python principiantes")

    def test_acepta_none_y_valores_no_string(self) -> None:
        """Comprueba entradas vacías y valores que todavía no son cadenas."""

        self.assertEqual(limpiar_texto(None, palabras_vacias={"de"}), "")
        self.assertEqual(limpiar_texto(123, palabras_vacias={"de"}), "123")


if __name__ == "__main__":
    # También permite ejecutar directamente: python tests/test_limpieza_texto.py
    unittest.main()
