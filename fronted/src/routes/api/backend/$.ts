import { createFileRoute } from "@tanstack/react-router";

// Proxy genérico hacia el backend real (FastAPI en Render).
// El navegador llama a /api/backend/<ruta> (mismo origen, sin CORS) y el
// servidor reenvía la petición tal cual a  https://<backend>/<ruta>.
//
// Rutas del backend (swagger /docs):
//   POST /contenido/archivo     subir y clasificar archivo (multipart: file, autor, tipo)
//   POST /contenido/clasificar  clasificar texto suelto (JSON: texto, top_n_palabras_clave)
//   GET  /contenido             listar documentos (offset, limit, categoria, autor, tipo_contenido)
//   GET  /contenido/{id}        detalle de un documento
//   GET  /buscar                búsqueda (q, categoria, autor, tipo_contenido, offset, limit)

const BACKEND_POR_DEFECTO = "https://g9-latam-team-25.onrender.com";

const RUTAS_PERMITIDAS = [
  /^contenido$/,
  /^contenido\/archivo$/,
  /^contenido\/clasificar$/,
  /^contenido\/\d+$/,
  /^buscar$/,
  /^health$/,
];

async function reenviar(request: Request, splat: string) {
  const ruta = (splat ?? "").replace(/^\/+/, "");
  if (!RUTAS_PERMITIDAS.some((r) => r.test(ruta))) {
    return Response.json({ error: "Ruta no permitida" }, { status: 404 });
  }

  const backendUrl = process.env["BACKEND_API_URL"] ?? BACKEND_POR_DEFECTO;
  const query = new URL(request.url).search;

  try {
    const headers: Record<string, string> = {};
    const contentType = request.headers.get("content-type");
    if (contentType) headers["Content-Type"] = contentType;

    const res = await fetch(`${backendUrl}/${ruta}${query}`, {
      method: request.method,
      headers,
      body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer(),
    });

    const text = await res.text();
    return new Response(text, {
      status: res.status,
      headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
    });
  } catch {
    return Response.json(
      { error: "No se pudo conectar con el backend. Inténtalo de nuevo en unos segundos." },
      { status: 502 },
    );
  }
}

export const Route = createFileRoute("/api/backend/$")({
  server: {
    handlers: {
      GET: async ({ request, params }) => reenviar(request, params._splat ?? ""),
      POST: async ({ request, params }) => reenviar(request, params._splat ?? ""),
    },
  },
});
