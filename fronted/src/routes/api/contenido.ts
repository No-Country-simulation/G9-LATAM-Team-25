import { createFileRoute } from "@tanstack/react-router";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export const Route = createFileRoute("/api/contenido")({
  server: {
    handlers: {
      OPTIONS: async () => new Response(null, { status: 204, headers: CORS }),
      GET: async ({ request }) => {
        const backendUrl =
          process.env["BACKEND_API_URL"] ?? "https://g9-latam-team-25.onrender.com";

        try {
          const incoming = new URL(request.url);
          const res = await fetch(`${backendUrl}/contenido${incoming.search}`);
          const text = await res.text();
          return new Response(text, {
            status: res.status,
            headers: { "Content-Type": "application/json", ...CORS },
          });
        } catch {
          return new Response(
            JSON.stringify({ error: "No se pudo conectar con el backend de contenidos." }),
            { status: 502, headers: { "Content-Type": "application/json", ...CORS } },
          );
        }
      },
    },
  },
});
