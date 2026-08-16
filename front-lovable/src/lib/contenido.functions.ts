import { createServerFn } from "@tanstack/react-start";

export type Clasificacion = {
  categoria: string;
  probabilidad: number;
  palabrasClave: string[];
  resumen: string;
};

const CATEGORIAS: { nombre: string; terminos: string[] }[] = [
  {
    nombre: "Documentación técnica",
    terminos: ["api", "endpoint", "documentación", "docs", "referencia", "manual", "spec", "swagger"],
  },
  {
    nombre: "Tutorial / Guía",
    terminos: ["tutorial", "guía", "paso", "cómo", "instalar", "configurar", "ejemplo", "empezar"],
  },
  {
    nombre: "Apuntes personales",
    terminos: ["apunte", "nota", "recordar", "idea", "borrador", "pendiente", "todo"],
  },
  {
    nombre: "Artículo / Investigación",
    terminos: ["artículo", "análisis", "estudio", "comparativa", "tendencia", "opinión", "paper"],
  },
  {
    nombre: "Infraestructura / DevOps",
    terminos: ["docker", "kubernetes", "servidor", "deploy", "ci", "cd", "nginx", "cloud", "pipeline"],
  },
  {
    nombre: "Datos / Base de datos",
    terminos: ["sql", "base de datos", "postgres", "query", "tabla", "índice", "migración", "schema"],
  },
];

const VACIAS = new Set([
  "para","que","con","este","esta","como","cómo","los","las","del","una","uno","por","the","and","from",
  "sobre","más","pero","sus","son","fue","han","hay","muy","cuando","donde","también","entre","todo",
]);

/**
 * Simulación local del endpoint /contenido.
 * Cuando el servicio real esté disponible, basta con reemplazar el cuerpo
 * del handler por un fetch a `${process.env.CONTENIDO_API_URL}/contenido`.
 */
export const clasificarContenido = createServerFn({ method: "POST" })
  .inputValidator((input: { texto: string }) => {
    const texto = (input?.texto ?? "").trim();
    if (!texto) throw new Error("El texto no puede estar vacío");
    return { texto: texto.slice(0, 8000) };
  })
  .handler(async ({ data }): Promise<Clasificacion> => {
    await new Promise((r) => setTimeout(r, 650));

    const texto = data.texto.toLowerCase();
    const puntajes = CATEGORIAS.map((c) => ({
      nombre: c.nombre,
      puntaje: c.terminos.reduce((acc, t) => acc + (texto.includes(t) ? 1 : 0), 0),
    })).sort((a, b) => b.puntaje - a.puntaje);

    const mejor = puntajes[0];
    const total = puntajes.reduce((a, p) => a + p.puntaje, 0);
    const probabilidad =
      total === 0 ? 0.42 : Math.min(0.98, 0.55 + (mejor.puntaje / total) * 0.43);

    const frecuencias = new Map<string, number>();
    for (const palabra of texto.match(/[a-záéíóúñü]{4,}/g) ?? []) {
      if (VACIAS.has(palabra)) continue;
      frecuencias.set(palabra, (frecuencias.get(palabra) ?? 0) + 1);
    }
    const palabrasClave = [...frecuencias.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([p]) => p);

    return {
      categoria: mejor.puntaje === 0 ? "Contenido general" : mejor.nombre,
      probabilidad: Number(probabilidad.toFixed(2)),
      palabrasClave,
      resumen: data.texto.slice(0, 180) + (data.texto.length > 180 ? "…" : ""),
    };
  });
