"""Pruebas unitarias del resumen extractivo compartido."""

import unittest

from shared.resumen_automatico import dividir_oraciones, generar_resumen
from shared.texto_visible import contiene_html_presentacion, extraer_texto_visible


class ExtraerTextoVisibleTests(unittest.TestCase):
    def test_conserva_puntuacion_inline_y_bloques_html(self):
        texto = (
            "<p><strong>Python</strong>. ¿Funciona con C++ y ASP.NET?</p>"
            "<p>Backend &amp; APIs.</p>"
        )

        self.assertEqual(
            extraer_texto_visible(texto),
            "Python. ¿Funciona con C++ y ASP.NET?\n\nBackend & APIs.",
        )

    def test_decodifica_html_escapado_y_descarta_codigo_no_visible(self):
        texto = (
            "&lt;p&gt;Programaci&#243;n con List&amp;lt;T&amp;gt;.&lt;/p&gt;"
            "<head><title>No visible</title><meta charset='utf-8'></head>"
            "<img src='curso.png' alt='imagen decorativa'>"
            "<style>.oculto { color: red; }</style>"
            "<script>alert('no visible')</script>"
        )

        self.assertEqual(
            extraer_texto_visible(texto),
            "Programación con List<T>.",
        )

    def test_separa_contenedores_y_detecta_html_de_presentacion(self):
        texto = (
            "<html><body><form>Primero</form><form>Segundo</form>"
            "<select><option>Uno</option><option>Dos</option></select>"
            "</body></html>"
        )

        visible = extraer_texto_visible(texto)

        self.assertEqual(visible.split(), ["Primero", "Segundo", "Uno", "Dos"])
        self.assertFalse(contiene_html_presentacion(visible))
        self.assertTrue(contiene_html_presentacion(texto))
        self.assertFalse(contiene_html_presentacion("List<T> y <version>2</version>"))

    def test_detector_no_confunde_codigo_ni_comparaciones_con_html(self):
        casos = (
            "#include <time.h>",
            "x < a",
            "<base-config>dato</base-config>",
        )

        for texto in casos:
            with self.subTest(texto=texto):
                self.assertFalse(contiene_html_presentacion(texto))

    def test_elimina_etiquetas_svg_y_conserva_su_texto_visible(self):
        texto = '<svg><path d="M0 0"></path><text>Diagrama</text></svg>'

        visible = extraer_texto_visible(texto)

        self.assertEqual(visible, "Diagrama")
        self.assertFalse(contiene_html_presentacion(visible))

    def test_descarta_etiquetas_no_visibles_autocerradas(self):
        texto = (
            "Antes<script/><style/><template/><title/><head/><noscript/>Después"
        )

        visible = extraer_texto_visible(texto)

        self.assertEqual(visible, "AntesDespués")
        self.assertFalse(contiene_html_presentacion(visible))

    def test_conserva_mayusculas_de_xml_desconocido(self):
        texto = '<MyTag data-ID="7">Dato</MyTag>'

        self.assertEqual(extraer_texto_visible(texto), texto)


class DividirOracionesTests(unittest.TestCase):
    def test_conserva_abreviaturas_decimales_y_puntuacion(self):
        texto = (
            "El Dr. Pérez midió 3.14 metros. "
            "¿El resultado fue estable? Sí, lo fue."
        )

        self.assertEqual(
            dividir_oraciones(texto),
            [
                "El Dr. Pérez midió 3.14 metros.",
                "¿El resultado fue estable?",
                "Sí, lo fue.",
            ],
        )

    def test_tratamiento_puede_cerrar_una_oracion(self):
        casos = (
            (
                "Se reunió con el Dr. Luego regresó al equipo.",
                ["Se reunió con el Dr.", "Luego regresó al equipo."],
            ),
            (
                "Conversó con la Sra. Después documentó el acuerdo.",
                ["Conversó con la Sra.", "Después documentó el acuerdo."],
            ),
        )

        for texto, esperado in casos:
            with self.subTest(texto=texto):
                self.assertEqual(dividir_oraciones(texto), esperado)

    def test_distingue_inicial_personal_de_opcion_tecnica(self):
        self.assertEqual(
            dividir_oraciones("El autor J. Pérez publicó la guía."),
            ["El autor J. Pérez publicó la guía."],
        )
        self.assertEqual(
            dividir_oraciones("Seleccione la opción A. Luego continúe."),
            ["Seleccione la opción A.", "Luego continúe."],
        )
        self.assertEqual(
            dividir_oraciones(
                "La respuesta correcta es B. Después ejecute las pruebas."
            ),
            [
                "La respuesta correcta es B.",
                "Después ejecute las pruebas.",
            ],
        )

    def test_reconoce_cierre_de_comillas(self):
        texto = 'Ella preguntó: "¿Funciona?" El equipo respondió que sí.'

        self.assertEqual(
            dividir_oraciones(texto),
            ['Ella preguntó: "¿Funciona?"', "El equipo respondió que sí."],
        )

    def test_reconoce_cierre_de_comillas_al_final_del_texto(self):
        casos = (
            ('Ella preguntó: "¿Funciona?"', ['Ella preguntó: "¿Funciona?"']),
            ("El equipo respondió: 'Sí.'", ["El equipo respondió: 'Sí.'"]),
            ("La guía concluye: «Listo.»", ["La guía concluye: «Listo.»"]),
        )

        for texto, esperado in casos:
            with self.subTest(texto=texto):
                self.assertEqual(dividir_oraciones(texto), esperado)

    def test_distingue_una_comilla_de_apertura_sin_espacio(self):
        texto = 'La API responde."Otra frase comienza aquí."'

        self.assertEqual(
            dividir_oraciones(texto),
            ['La API responde.', '"Otra frase comienza aquí."'],
        )

    def test_reconoce_comilla_de_cierre_sin_espacio_posterior(self):
        texto = 'Ella preguntó: "¿Funciona?"El equipo respondió que sí.'

        self.assertEqual(
            dividir_oraciones(texto),
            ['Ella preguntó: "¿Funciona?"', "El equipo respondió que sí."],
        )

    def test_apostrofo_en_palabra_no_se_confunde_con_comilla(self):
        texto = "L'utilisateur responde.'Otra frase comienza aquí.'"

        self.assertEqual(
            dividir_oraciones(texto),
            ["L'utilisateur responde.", "'Otra frase comienza aquí.'"],
        )

    def test_cierre_de_comillas_y_parentesis_antes_de_otro_bloque(self):
        texto = (
            'Según la ayuda de Jenkins (el botón "?")\n\n'
            "La expresión utiliza cinco campos."
        )

        self.assertEqual(
            dividir_oraciones(texto),
            [
                'Según la ayuda de Jenkins (el botón "?")',
                "La expresión utiliza cinco campos.",
            ],
        )

    def test_cierre_de_comilla_en_chunk_antes_de_otro_bloque(self):
        texto = (
            'Valor citado termina [prod|preprod|test]."\n\n'
            "Siguiente unidad estable."
        )

        self.assertEqual(
            dividir_oraciones(texto),
            [
                'Valor citado termina [prod|preprod|test]."',
                "Siguiente unidad estable.",
            ],
        )

    def test_conserva_abreviaturas_compuestas_y_etcetera(self):
        texto = (
            "La agencia de EE. UU. usa controles, p. ej. cifrado y firmas. "
            "Protege claves, certificados, etc. y registra cada acceso."
        )

        self.assertEqual(
            dividir_oraciones(texto),
            [
                "La agencia de EE. UU. usa controles, p. ej. cifrado y firmas.",
                "Protege claves, certificados, etc. y registra cada acceso.",
            ],
        )

    def test_abreviatura_compuesta_admite_nombre_propio_tecnico(self):
        texto = (
            "El orquestador admite alternativas, p. ej. Kubernetes y Nomad. "
            "En EE. UU. Microsoft opera varias regiones cloud."
        )

        self.assertEqual(
            dividir_oraciones(texto),
            [
                "El orquestador admite alternativas, p. ej. Kubernetes y "
                "Nomad.",
                "En EE. UU. Microsoft opera varias regiones cloud.",
            ],
        )

    def test_abreviatura_puede_cerrar_una_oracion(self):
        texto = "Esto se define en el art. La norma entra mañana."

        self.assertEqual(
            dividir_oraciones(texto),
            ["Esto se define en el art.", "La norma entra mañana."],
        )

    def test_separa_oraciones_sin_espacio(self):
        texto = "La API valida la entrada.El servicio devuelve JSON."

        self.assertEqual(
            dividir_oraciones(texto),
            ["La API valida la entrada.", "El servicio devuelve JSON."],
        )

    def test_conserva_lineas_envueltas_y_separa_vinetas(self):
        texto = (
            "Docker empaqueta una aplicación con todas\n"
            "sus dependencias para ejecutarla de forma consistente.\n\n"
            "- Kubernetes distribuye los contenedores.\n"
            "- Prometheus recopila métricas."
        )

        self.assertEqual(
            dividir_oraciones(texto),
            [
                "Docker empaqueta una aplicación con todas sus dependencias "
                "para ejecutarla de forma consistente.",
                "- Kubernetes distribuye los contenedores.",
                "- Prometheus recopila métricas.",
            ],
        )

    def test_lista_numerada_no_separa_el_marcador_del_contenido(self):
        texto = "1. Introducción\n2. Arquitectura\n3. Despliegue"

        self.assertEqual(
            dividir_oraciones(texto),
            ["1. Introducción", "2. Arquitectura", "3. Despliegue"],
        )

    def test_conserva_nombres_del_ecosistema_dotnet(self):
        texto = (
            "ASP.NET permite construir APIs web. "
            "VB.NET también se ejecuta sobre la plataforma."
        )

        self.assertEqual(
            dividir_oraciones(texto),
            [
                "ASP.NET permite construir APIs web.",
                "VB.NET también se ejecuta sobre la plataforma.",
            ],
        )


class GenerarResumenTests(unittest.TestCase):
    def test_texto_vacio_devuelve_cadena_vacia(self):
        self.assertEqual(generar_resumen("  \n\t  "), "")

    def test_documento_corto_se_devuelve_completo_y_en_orden(self):
        texto = "Primera idea importante. Segunda idea complementaria."

        self.assertEqual(generar_resumen(texto), texto)

    def test_documento_corto_con_duplicado_se_devuelve_completo(self):
        texto = "Misma oración. Misma oración."

        self.assertEqual(generar_resumen(texto), texto)

    def test_bloque_largo_sin_puntuacion_no_se_devuelve_completo(self):
        texto = " ".join(f"concepto{i}" for i in range(1, 121))

        resumen = generar_resumen(texto, n_oraciones=3)

        self.assertNotEqual(resumen, texto)
        self.assertLess(len(resumen.split()), len(texto.split()))
        self.assertLessEqual(len(dividir_oraciones(resumen)), 3)
        self.assertTrue(
            all(fragmento in texto for fragmento in dividir_oraciones(resumen))
        )

    def test_token_muy_largo_no_produce_recursion_infinita(self):
        token = "x" * 1000
        dos_tokens = f"{'a' * 400} {'b' * 400}"

        self.assertEqual(dividir_oraciones(token), [token])
        self.assertEqual(dividir_oraciones(dos_tokens), dos_tokens.split())

    def test_tres_oraciones_extensas_no_devuelven_el_documento_completo(self):
        texto = (
            "La arquitectura distribuye las solicitudes entre varios servicios "
            "independientes y registra métricas detalladas para facilitar el "
            "diagnóstico durante incidentes de producción complejos. "
            "El pipeline valida cada cambio mediante pruebas unitarias, análisis "
            "estático, controles de seguridad y despliegues progresivos antes de "
            "promover una versión al entorno principal. "
            "La observabilidad combina registros, trazas y alertas para que el "
            "equipo pueda identificar regresiones, comparar versiones y recuperar "
            "el servicio con rapidez cuando aparece una degradación inesperada."
        )

        resumen = generar_resumen(texto, n_oraciones=3, titulo="DevOps")

        self.assertGreater(len(texto), 500)
        self.assertNotEqual(resumen, texto)
        self.assertEqual(len(dividir_oraciones(resumen)), 2)

    def test_unir_bloques_no_crea_una_oracion_adicional(self):
        texto = (
            "Primera oración.\n\n"
            "El código invoca java.lang.\n\n"
            "4. cadena.toLongOrNull(10)"
        )

        resumen = generar_resumen(texto, n_oraciones=3)

        self.assertEqual(dividir_oraciones(resumen), dividir_oraciones(texto))
        self.assertEqual(len(dividir_oraciones(resumen)), 3)

    def test_html_no_llega_al_resumen_y_se_respeta_el_maximo(self):
        texto = (
            "&lt;p&gt;Docker empaqueta aplicaciones.&lt;/p&gt;"
            "<p>Kubernetes distribuye contenedores.</p>"
            "<p>Prometheus recopila métricas.</p>"
            "<p>Grafana presenta paneles &amp; alertas.</p>"
            "<script>alert('oculto')</script>"
        )

        resumen = generar_resumen(texto, n_oraciones=3, titulo="DevOps")

        self.assertLessEqual(len(dividir_oraciones(resumen)), 3)
        self.assertNotRegex(resumen, r"<\s*/?\s*[A-Za-z][^>]*>")
        self.assertNotIn("&lt;", resumen)
        self.assertNotIn("&amp;", resumen)
        self.assertNotIn("oculto", resumen)

    def test_selecciona_tres_oraciones_extractivas_en_orden_original(self):
        texto = (
            "La inteligencia artificial ayuda a procesar grandes volúmenes de datos. "
            "Los equipos primero deben definir un problema de negocio concreto. "
            "La calidad de los datos determina gran parte del resultado del modelo. "
            "Una evaluación continua permite detectar errores y sesgos. "
            "Las personas expertas validan las recomendaciones antes de aplicarlas. "
            "La documentación facilita el mantenimiento de cada solución."
        )

        resumen = generar_resumen(texto)
        originales = dividir_oraciones(texto)
        seleccionadas = dividir_oraciones(resumen)
        posiciones = [originales.index(oracion) for oracion in seleccionadas]

        self.assertEqual(len(seleccionadas), 3)
        self.assertTrue(all(oracion in originales for oracion in seleccionadas))
        self.assertEqual(posiciones, sorted(posiciones))

    def test_titulo_refuerza_la_oracion_relacionada(self):
        texto = (
            "React permite construir componentes de interfaz. "
            "PostgreSQL crea índices para acelerar consultas. "
            "Kubernetes distribuye contenedores en un clúster. "
            "Swift se utiliza para desarrollar aplicaciones móviles."
        )

        resumen = generar_resumen(
            texto,
            n_oraciones=1,
            titulo="Índices y consultas en PostgreSQL",
        )

        self.assertEqual(
            resumen,
            "PostgreSQL crea índices para acelerar consultas.",
        )

    def test_titulo_csharp_conserva_su_senal(self):
        texto = (
            "Python facilita el análisis de datos. "
            "Java se usa en aplicaciones empresariales. "
            "C# permite construir servicios sobre .NET. "
            "Rust prioriza la seguridad de memoria."
        )

        resumen = generar_resumen(texto, n_oraciones=1, titulo="C# y .NET")

        self.assertEqual(
            resumen,
            "C# permite construir servicios sobre .NET.",
        )

    def test_cplusplus_y_csharp_no_se_tratan_como_duplicados(self):
        texto = "C++. C#. Rust. Java."

        resumen = generar_resumen(texto, n_oraciones=3, titulo="C#")

        self.assertIn("C#.", dividir_oraciones(resumen))

    def test_mmr_evitar_oraciones_casi_repetidas(self):
        texto = (
            "Docker empaqueta aplicaciones y dependencias en contenedores. "
            "Docker crea contenedores con aplicaciones y sus dependencias. "
            "Kubernetes distribuye las réplicas entre varios nodos. "
            "El pipeline ejecuta pruebas antes de publicar una imagen. "
            "Prometheus recopila métricas del servicio en producción."
        )

        resumen = generar_resumen(
            texto,
            n_oraciones=3,
            titulo="Despliegue de contenedores con Docker",
        )

        repetidas = (
            "Docker empaqueta aplicaciones y dependencias en contenedores.",
            "Docker crea contenedores con aplicaciones y sus dependencias.",
        )
        self.assertEqual(len(dividir_oraciones(resumen)), 3)
        self.assertLessEqual(sum(oracion in resumen for oracion in repetidas), 1)

    def test_elimina_duplicados_exactos(self):
        texto = (
            "Los sensores registran la temperatura. "
            "Los sensores registran la temperatura. "
            "Una alerta avisa cuando cambia el valor. "
            "El equipo revisa la medición."
        )

        resumen = generar_resumen(texto, n_oraciones=3)

        self.assertEqual(
            resumen.count("Los sensores registran la temperatura."),
            1,
        )
        self.assertEqual(len(dividir_oraciones(resumen)), 3)

    def test_vocabulario_vacio_usa_fallback_determinista(self):
        texto = "De la que el. En y a los. Por un para con. Una su al lo."

        self.assertEqual(
            generar_resumen(texto, n_oraciones=2),
            "De la que el. En y a los.",
        )

    def test_unidades_simbolicas_usan_fallback_sin_quedar_vacias(self):
        texto = "😀. 😃. 😄. 😁."

        resumen = generar_resumen(texto, n_oraciones=3)

        self.assertEqual(resumen, "😀. 😃. 😄.")
        self.assertEqual(len(dividir_oraciones(resumen)), 3)

    def test_resultado_es_determinista(self):
        texto = (
            "FastAPI expone endpoints HTTP. "
            "PostgreSQL almacena registros relacionales. "
            "React renderiza componentes de interfaz. "
            "Docker ejecuta servicios en contenedores."
        )

        primero = generar_resumen(texto, n_oraciones=2)
        segundo = generar_resumen(texto, n_oraciones=2)

        self.assertEqual(primero, segundo)

    def test_valida_tipos_y_numero_de_oraciones(self):
        with self.assertRaises(TypeError):
            generar_resumen(None)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            dividir_oraciones(None)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            generar_resumen("Texto.", n_oraciones=2.5)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            generar_resumen("Texto.", n_oraciones=True)
        with self.assertRaises(ValueError):
            generar_resumen("Texto.", n_oraciones=0)
        with self.assertRaises(TypeError):
            generar_resumen("Texto.", titulo=123)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
