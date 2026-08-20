import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import logo from "@/assets/honeyguard-logo.png";
import {
  clasificarTextoContenido,
  type RespuestaClasificacionTexto,
} from "@/lib/contenido-api";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "HoneyGuard — Clasifica y organiza tu contenido técnico" },
      {
        name: "description",
        content:
          "HoneyGuard clasifica documentación, artículos, apuntes y tutoriales para que reutilices tu conocimiento técnico en segundos.",
      },
      { property: "og:title", content: "HoneyGuard — Clasifica y organiza tu contenido técnico" },
      {
        property: "og:description",
        content:
          "HoneyGuard clasifica documentación, artículos, apuntes y tutoriales para que reutilices tu conocimiento técnico en segundos.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Index,
});

function Index() {
  const [texto, setTexto] = useState("");

  const clasificacion = useMutation<RespuestaClasificacionTexto, Error>({
    mutationFn: () => clasificarTextoContenido({ texto: texto.trim(), top_n_palabras_clave: 8 }),
  });

  function enviarClasificacion() {
    if (texto.trim().length > 0) clasificacion.mutate();
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex max-w-3xl flex-col gap-10 px-6 py-14">
        <header className="flex flex-col items-center text-center">
          <img
            src={logo}
            alt="Logo de HoneyGuard: un tejón abrazando un panal dorado"
            className="h-40 w-40 rounded-3xl object-cover"
            style={{ boxShadow: "var(--honey-glow)" }}
          />
          <h1 className="mt-6 text-4xl font-bold tracking-tight">
            Honey<span className="text-primary">Guard</span>
          </h1>
          <p className="mt-3 max-w-md text-sm text-muted-foreground">
            Clasifica, organiza y reutiliza tu contenido técnico: documentación, artículos,
            apuntes y tutoriales.
          </p>
          <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/subir"
              className="rounded-xl border border-border px-5 py-2 text-sm font-medium hover:border-primary"
            >
              Subir archivo (.pdf / .txt) →
            </Link>
            <Link
              to="/buscar"
              className="rounded-xl border border-border px-5 py-2 text-sm font-medium hover:border-primary"
            >
              Buscar contenidos →
            </Link>
          </div>
        </header>

        <section
          className="rounded-2xl border border-border p-6"
          style={{ backgroundColor: "var(--surface-elevated)" }}
        >
          <div className="flex flex-col gap-1">
            <h2 className="text-lg font-semibold text-foreground">Clasificar texto</h2>
            <p className="text-sm text-muted-foreground">
              Pega texto directamente y HoneyGuard lo clasificará con el modelo de Machine Learning
              del backend, sin necesidad de cargar un archivo.
            </p>
          </div>

          <textarea
            value={texto}
            onChange={(event) => {
              setTexto(event.target.value);
              if (clasificacion.isSuccess || clasificacion.isError) clasificacion.reset();
            }}
            rows={8}
            placeholder="Pega aquí documentación, apuntes, un artículo o cualquier texto técnico…"
            className="mt-5 w-full resize-y rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none transition-colors placeholder:text-muted-foreground focus:border-primary"
          />

          {clasificacion.isError && (
            <p className="mt-3 text-sm text-destructive">
              {clasificacion.error.message || "No se pudo clasificar el texto."}
            </p>
          )}

          <button
            type="button"
            onClick={enviarClasificacion}
            disabled={!texto.trim() || clasificacion.isPending}
            className="mt-4 w-full rounded-xl px-6 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity disabled:opacity-40"
            style={{ backgroundImage: "var(--gradient-honey)" }}
          >
            {clasificacion.isPending ? "Clasificando…" : "Clasificar texto"}
          </button>

          {clasificacion.data && (
            <div className="mt-6 grid gap-4 rounded-2xl border border-border bg-card p-5">
              <div>
                <p className="text-xs uppercase tracking-widest text-muted-foreground">Categoría</p>
                <p className="mt-1 text-xl font-semibold text-primary">
                  {clasificacion.data.categoria}
                </p>
              </div>

              <div>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs uppercase tracking-widest text-muted-foreground">
                    Probabilidad
                  </p>
                  <span className="text-sm font-semibold">
                    {Math.round(clasificacion.data.probabilidad * 100)}%
                  </span>
                </div>
                <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${clasificacion.data.probabilidad * 100}%`,
                      backgroundImage: "var(--gradient-honey)",
                    }}
                  />
                </div>
              </div>

              <div>
                <p className="text-xs uppercase tracking-widest text-muted-foreground">
                  Palabras clave
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {clasificacion.data.palabras_clave.map((palabra) => (
                    <span
                      key={palabra}
                      className="rounded-full border border-border bg-secondary px-3 py-1 text-sm"
                    >
                      #{palabra}
                    </span>
                  ))}
                </div>
              </div>

              {clasificacion.data.requiere_revision && (
                <p className="text-sm text-muted-foreground">
                  La confianza del modelo es baja; conviene revisar manualmente la categoría.
                </p>
              )}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
