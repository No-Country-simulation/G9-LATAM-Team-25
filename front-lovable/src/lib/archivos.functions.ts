import { createServerFn } from "@tanstack/react-start";

export type CampoExtraido = {
  clave: string;
  etiqueta: string;
  valor: string;
  confianza: number; // 0..1
};

export type DuplicadoDetectado = {
  titulo: string;
  similitud: number; // 0..1
};

export type ExtraccionArchivo = {
  archivo: string;
  campos: CampoExtraido[];
  duplicado?: DuplicadoDetectado;
};

export type GuardadoResultado =
  | { ok: true; id: string; archivo: string }
  | { ok: false; duplicado: DuplicadoDetectado };

const VACIAS = new Set([
  "para", "que", "con", "este", "esta", "como", "cómo", "los", "las", "del", "una", "uno",
  "por", "the", "and", "from", "sobre", "más", "pero", "sus", "son", "fue", "han", "hay",
  "muy", "cuando", "donde", "también", "entre", "todo",
]);

function palabrasClave(texto: string, max = 6) {
  const frecuencias = new Map<string, number>();
  for (const palabra of texto.toLowerCase().match(/[a-záéíóúñü]{4,}/g) ?? []) {
    if (VACIAS.has(palabra)) continue;
    frecuencias.set(palabra, (frecuencias.get(palabra) ?? 0) + 1);
  }
  return [...frecuencias.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, max)
    .map(([p]) => p);
}

function categoriaDe(texto: string): { valor: string; confianza: number } {
  const t = texto.toLowerCase();
  const reglas: [string, string[]][] = [
    ["Documentación técnica", ["api", "endpoint", "documentación", "manual", "referencia"]],
    ["Tutorial / Guía", ["tutorial", "guía", "paso", "instalar", "configurar"]],
    ["Apuntes personales", ["apunte", "nota", "borrador", "pendiente"]],
    ["Artículo / Investigación", ["artículo", "análisis", "estudio", "paper"]],
    ["Infraestructura / DevOps", ["docker", "kubernetes", "deploy", "pipeline", "nginx"]],
    ["Datos / Base de datos", ["sql", "postgres", "query", "tabla", "schema"]],
  ];
  let mejor = { valor: "Contenido general", confianza: 0.41 };
  for (const [nombre, terminos] of reglas) {
    const aciertos = terminos.filter((x) => t.includes(x)).length;
    if (aciertos > 0) {
      const confianza = Math.min(0.97, 0.55 + aciertos * 0.1);
      if (confianza > mejor.confianza) mejor = { valor: nombre, confianza };
    }
  }
  return mejor;
}

/**
 * Simulación del endpoint de carga de archivo del backend (Python).
 * Para conectarlo de verdad, reemplaza el cuerpo del handler por:
 *
 *   const apiUrl = process.env['CONTENIDO_API_URL'] ?? 'http://localhost:8000';
 *   const res = await fetch(`${apiUrl}/archivos`, { method: 'POST', body: ... });
 *   return res.json();
 *
 * Si el backend responde con similitud >= 0.8, devuelve `duplicado` en lugar de campos.
 */
export const analizarArchivo = createServerFn({ method: "POST" })
  .inputValidator((input: { nombre: string; tipo: string; tamano: number; texto: string }) => {
    const nombre = (input?.nombre ?? "").trim();
    if (!nombre) throw new Error("Falta el nombre del archivo");
    if (!/\.(pdf|txt)$/i.test(nombre)) throw new Error("Solo se aceptan archivos .pdf o .txt");
    if ((input.tamano ?? 0) > 10 * 1024 * 1024) throw new Error("El archivo supera los 10 MB");
    return {
      nombre: nombre.slice(0, 200),
      tipo: (input.tipo ?? "").slice(0, 100),
      tamano: input.tamano ?? 0,
      texto: (input.texto ?? "").slice(0, 20000),
    };
  })
  .handler(async ({ data }): Promise<ExtraccionArchivo> => {
    await new Promise((r) => setTimeout(r, 800));

    // Simulación: el backend detecta duplicado con similitud >= 80%.
    const textoBase = (data.texto || data.nombre).toLowerCase();
    if (textoBase.includes("duplicado")) {
      return {
        archivo: data.nombre,
        campos: [],
        duplicado: {
          titulo: "Guía completa de Docker para desarrolladores",
          similitud: 0.87,
        },
      };
    }

    const esPdf = /\.pdf$/i.test(data.nombre);
    const texto = data.texto;
    const cat = categoriaDe(texto || data.nombre);
    const claves = palabrasClave(texto || data.nombre);

    const tituloCrudo =
      texto.split("\n").map((l) => l.trim()).find((l) => l.length > 3) ??
      data.nombre.replace(/\.[^.]+$/, "");

    const campos: CampoExtraido[] = [
      {
        clave: "titulo",
        etiqueta: "Título",
        valor: tituloCrudo.slice(0, 120),
        confianza: texto ? 0.88 : 0.45,
      },
      { clave: "categoria", etiqueta: "Categoría", valor: cat.valor, confianza: cat.confianza },
      {
        clave: "autor",
        etiqueta: "Autor",
        valor: (texto.match(/autor:\s*(.+)/i)?.[1] ?? "").trim(),
        confianza: texto.match(/autor:/i) ? 0.82 : 0.28,
      },
      {
        clave: "fecha",
        etiqueta: "Fecha",
        valor: texto.match(/\d{4}-\d{2}-\d{2}/)?.[0] ?? new Date().toISOString().slice(0, 10),
        confianza: texto.match(/\d{4}-\d{2}-\d{2}/) ? 0.91 : 0.35,
      },
      {
        clave: "palabrasClave",
        etiqueta: "Palabras clave",
        valor: claves.join(", "),
        confianza: claves.length >= 4 ? 0.79 : 0.5,
      },
      {
        clave: "resumen",
        etiqueta: "Resumen",
        valor: texto ? texto.replace(/\s+/g, " ").slice(0, 220) : "Sin texto extraído del PDF.",
        confianza: texto ? 0.72 : esPdf ? 0.3 : 0.4,
      },
    ];

    return { archivo: data.nombre, campos };
  });

/** Guardado definitivo, después de que el usuario confirma los campos. */
export const guardarContenido = createServerFn({ method: "POST" })
  .inputValidator((input: { archivo: string; campos: Record<string, string> }) => {
    const archivo = (input?.archivo ?? "").trim();
    if (!archivo) throw new Error("Falta el archivo");
    const campos = input?.campos ?? {};
    if (!(campos["titulo"] ?? "").trim()) throw new Error("El título es obligatorio");
    return { archivo, campos };
  })
  .handler(async ({ data }): Promise<GuardadoResultado> => {
    await new Promise((r) => setTimeout(r, 500));

    // Simulación: si el backend detecta duplicado al guardar, devuelve ok: false.
    const titulo = (data.campos["titulo"] ?? "").toLowerCase();
    if (titulo.includes("duplicado")) {
      return {
        ok: false as const,
        duplicado: {
          titulo: "Guía completa de Docker para desarrolladores",
          similitud: 0.87,
        },
      };
    }

    return { ok: true as const, id: `hg_${Date.now()}`, archivo: data.archivo };
  });
