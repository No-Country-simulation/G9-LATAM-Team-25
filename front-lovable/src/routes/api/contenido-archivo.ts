import { createFileRoute } from "@tanstack/react-router";

// Proxy al backend real (Render). El navegador sube el archivo a esta ruta
// (mismo origen, sin problemas de CORS) y el servidor lo reenvía al backend
// Python conservando el multipart tal cual.
//
// El backend expone: POST /contenido/archivo  (archivo + autor + tipo)
// Devuelve: { id, categoria, probabilidad, contenido_relacionado, autor, tipo, url_archivo, resumen }
// y guarda el contenido en ese mismo paso.

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export const Route = createFileRoute("/api/contenido-archivo")({
  server: {
    handlers: {
      OPTIONS: async () =>
        new Response(null, { status: 204, headers: CORS }),

      POST: async ({ request }) => {
        const backendUrl =
          process.env["BACKEND_API_URL"] ?? "https://g9-latam-team-25.onrender.com";

        try {
          const contentType = request.headers.get("content-type") ?? "";
          const body = await request.arrayBuffer();

          const res = await fetch(`${backendUrl}/contenido/archivo`, {
            method: "POST",
            headers: { "Content-Type": contentType },
            body,
          });

          const text = await res.text();
          return new Response(text, {
            status: res.status,
            headers: { "Content-Type": "application/json", ...CORS },
          });
        } catch (err) {
          return new Response(
            JSON.stringify({
              error:
                "No se pudo conectar con el backend. Inténtalo de nuevo en unos segundos.",
            }),
            { status: 502, headers: { "Content-Type": "application/json", ...CORS } },
          );
        }
      },
    },
  },
});
