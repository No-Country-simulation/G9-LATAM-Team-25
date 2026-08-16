import { createServerFn } from "@tanstack/react-start";

export type ResultadoBusqueda = {
  id: string;
  titulo: string;
  categoria: string;
  palabrasClave: string[];
  resumen: string;
  similitud: number; // 0..1
  fecha: string;
  autor?: string;
};

export type BusquedaResultados = {
  query: string;
  total: number;
  resultados: ResultadoBusqueda[];
};

// Catálogo de contenido simulado para la búsqueda local.
// Reemplazar por fetch al backend Python cuando esté listo.
const CATALOGO: ResultadoBusqueda[] = [
  {
    id: "hg_1001",
    titulo: "Guía completa de Docker para desarrolladores",
    categoria: "Infraestructura / DevOps",
    palabrasClave: ["docker", "contenedores", "despliegue", "imagen", "dockerfile"],
    resumen:
      "Introducción práctica a Docker: creación de imágenes, manejo de contenedores, volúmenes y redes para desarrollar y desplegar aplicaciones.",
    similitud: 0.92,
    fecha: "2024-03-15",
    autor: "Ana Martínez",
  },
  {
    id: "hg_1002",
    titulo: "Tutorial de PostgreSQL para principiantes",
    categoria: "Datos / Base de datos",
    palabrasClave: ["postgresql", "sql", "tablas", "queries", "índices"],
    resumen:
      "Tutorial paso a paso para instalar PostgreSQL, crear tablas, escribir consultas y optimizar índices básicos.",
    similitud: 0.85,
    fecha: "2024-05-22",
    autor: "Carlos López",
  },
  {
    id: "hg_1003",
    titulo: "Apuntes personales de React Hooks",
    categoria: "Apuntes personales",
    palabrasClave: ["react", "hooks", "usestate", "useeffect", "frontend"],
    resumen:
      "Resumen de los hooks más usados en React con ejemplos cortos y notas de uso para proyectos personales.",
    similitud: 0.78,
    fecha: "2024-07-10",
  },
  {
    id: "hg_1004",
    titulo: "Artículo: análisis de arquitectura limpia",
    categoria: "Artículo / Investigación",
    palabrasClave: ["arquitectura", "clean", "solid", "dominio", "capas"],
    resumen:
      "Análisis de los principios de arquitectura limpia, separación de responsabilidades y cómo aplicarlos en equipos pequeños.",
    similitud: 0.74,
    fecha: "2024-01-30",
    autor: "Diana Torres",
  },
  {
    id: "hg_1005",
    titulo: "Manual de referencia de la API REST interna",
    categoria: "Documentación técnica",
    palabrasClave: ["api", "rest", "endpoints", "autenticación", "json"],
    resumen:
      "Documentación de endpoints, métodos HTTP, códigos de respuesta y ejemplos de autenticación para la API interna.",
    similitud: 0.88,
    fecha: "2024-06-05",
    autor: "Equipo Backend",
  },
  {
    id: "hg_1006",
    titulo: "Cómo configurar un pipeline de CI/CD con GitHub Actions",
    categoria: "Tutorial / Guía",
    palabrasClave: ["github", "actions", "pipeline", "cicd", "automatización"],
    resumen:
      "Guía para crear workflows de integración continua, ejecutar tests automáticos y desplegar en servidores desde GitHub.",
    similitud: 0.81,
    fecha: "2024-08-12",
    autor: "Pedro Sánchez",
  },
];

function normalizar(texto: string) {
  return texto
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .split(/\s+/)
    .filter((t) => t.length > 2);
}

function calcularSimilitud(query: string[], item: ResultadoBusqueda) {
  const campos = [
    item.titulo,
    item.categoria,
    item.resumen,
    item.palabrasClave.join(" "),
    item.autor ?? "",
  ].join(" ");
  const tokens = normalizar(campos);
  const coincidencias = query.filter((q) => tokens.some((t) => t.includes(q) || q.includes(t))).length;
  return Math.min(0.98, Math.round((coincidencias / Math.max(1, query.length)) * 100) / 100);
}

/**
 * Simulación del endpoint de búsqueda del backend (Python).
 * Para conectarlo de verdad, reemplaza el cuerpo del handler por:
 *
 *   const apiUrl = process.env['CONTENIDO_API_URL'] ?? 'http://localhost:8000';
 *   const res = await fetch(`${apiUrl}/buscar?q=${encodeURIComponent(data.query)}`);
 *   return res.json();
 */
export const buscarContenidos = createServerFn({ method: "GET" })
  .inputValidator((input: { query: string }) => {
    const query = (input?.query ?? "").trim();
    if (!query) throw new Error("Ingresa un término de búsqueda");
    if (query.length > 200) throw new Error("La búsqueda es demasiado larga");
    return { query: query.slice(0, 200) };
  })
  .handler(async ({ data }): Promise<BusquedaResultados> => {
    await new Promise((r) => setTimeout(r, 600));

    const queryTokens = normalizar(data.query);
    if (queryTokens.length === 0) {
      return { query: data.query, total: 0, resultados: [] };
    }

    const resultados = CATALOGO.map((item) => ({
      ...item,
      similitud: calcularSimilitud(queryTokens, item),
    }))
      .filter((item) => item.similitud > 0)
      .sort((a, b) => b.similitud - a.similitud)
      .slice(0, 10);

    return { query: data.query, total: resultados.length, resultados };
  });
