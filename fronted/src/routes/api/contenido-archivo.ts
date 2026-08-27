import { createFileRoute } from "@tanstack/react-router";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export const Route = createFileRoute("/api/contenido-archivo")({
  server: {
    handlers: {
      OPTIONS: async () =>
        new Response(null, {
          status: 204,
          headers: CORS,
        }),

      POST: async ({ request }) => {
        const backendUrl =
          process.env["BACKEND_API_URL"] ?? "https://g9-latam-team-25.onrender.com";

        try {
          const formDataEntrada = await request.formData();

          const file = formDataEntrada.get("file");
          const autor = formDataEntrada.get("autor");
          const tipo = formDataEntrada.get("tipo");

          if (!(file instanceof File)) {
            return new Response(
              JSON.stringify({
                error: "El archivo no llegó correctamente al proxy del frontend.",
              }),
              {
                status: 400,
                headers: {
                  "Content-Type": "application/json",
                  ...CORS,
                },
              },
            );
          }

          const formDataBackend = new FormData();

          formDataBackend.append("file", file, file.name);

          formDataBackend.append(
            "autor",
            typeof autor === "string" && autor.trim() ? autor : "Desconocido",
          );

          formDataBackend.append("tipo", typeof tipo === "string" && tipo.trim() ? tipo : "otro");

          const res = await fetch(`${backendUrl}/contenido/archivo`, {
            method: "POST",
            body: formDataBackend,
          });

          const text = await res.text();

          return new Response(text, {
            status: res.status,
            headers: {
              "Content-Type": "application/json",
              ...CORS,
            },
          });
        } catch (err) {
          console.error("Error en proxy contenido-archivo:", err);

          return new Response(
            JSON.stringify({
              error: "No se pudo conectar con el backend. Inténtalo de nuevo en unos segundos.",
            }),
            {
              status: 502,
              headers: {
                "Content-Type": "application/json",
                ...CORS,
              },
            },
          );
        }
      },
    },
  },
});
