import { createFileRoute, Link } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import { buscarContenidos, type ResultadoBusqueda } from "@/lib/busqueda.functions";

export const Route = createFileRoute("/buscar")({
  head: () => ({
    meta: [
      { title: "Buscar contenidos — HoneyGuard" },
      {
        name: "description",
        content:
          "Busca documentación, artículos, apuntes y tutoriales guardados en HoneyGuard por texto o palabras clave.",
      },
      { property: "og:title", content: "Buscar contenidos — HoneyGuard" },
      {
        property: "og:description",
        content:
          "Busca documentación, artículos, apuntes y tutoriales guardados en HoneyGuard por texto o palabras clave.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: BuscarContenidos,
});

function colorSimilitud(similitud: number) {
  if (similitud >= 0.75) return "var(--confianza-alta)";
  if (similitud >= 0.5) return "var(--confianza-media)";
  return "var(--confianza-baja)";
}

function BuscarContenidos() {
  const [query, setQuery] = useState("");
  const buscar = useServerFn(buscarContenidos);
  const mutation = useMutation({
    mutationFn: (q: string) => buscar({ data: { query: q } }),
  });

  const resultados = mutation.data?.resultados ?? [];
  const buscado = mutation.isSuccess || mutation.isPending || mutation.isError;

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex max-w-3xl flex-col gap-8 px-6 py-12">
        <header className="flex flex-col gap-2">
          <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
            ← Volver a clasificar texto
          </Link>
          <h1 className="text-3xl font-bold tracking-tight">Buscar contenidos</h1>
          <p className="text-sm text-muted-foreground">
            Escribe palabras clave o una frase para encontrar documentación, tutoriales, apuntes y
            artículos relacionados.
          </p>
        </header>

        <section
          className="rounded-2xl border border-border p-6"
          style={{ backgroundColor: "var(--surface-elevated)" }}
        >
          <label htmlFor="busqueda" className="text-sm font-medium">
            Buscar por texto o palabras clave
          </label>
          <div className="mt-3 flex flex-col gap-3 sm:flex-row">
            <input
              id="busqueda"
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && query.trim()) {
                  mutation.mutate(query.trim());
                }
              }}
              placeholder="Ej: docker, postgresql, react hooks…"
              className="flex-1 rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-ring"
            />
            <button
              type="button"
              disabled={!query.trim() || mutation.isPending}
              onClick={() => mutation.mutate(query.trim())}
              className="rounded-xl px-6 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity disabled:opacity-40"
              style={{ backgroundImage: "var(--gradient-honey)" }}
            >
              {mutation.isPending ? "Buscando…" : "Buscar"}
            </button>
          </div>
          {mutation.isError && (
            <p className="mt-3 text-sm text-destructive">
              {(mutation.error as Error).message || "No se pudo realizar la búsqueda."}
            </p>
          )}
        </section>

        {buscado && resultados.length === 0 && !mutation.isPending && (
          <section className="rounded-2xl border border-border bg-card p-6 text-center">
            <p className="text-sm text-muted-foreground">
              No encontramos contenido relacionado con "{mutation.data?.query || query}".
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Prueba con otros términos o palabras clave más generales.
            </p>
          </section>
        )}

        {resultados.length > 0 && (
          <section className="flex flex-col gap-4">
            <div className="flex items-baseline justify-between gap-4">
              <h2 className="text-xl font-semibold">Resultados</h2>
              <span className="text-xs text-muted-foreground">
                {resultados.length} encontrado{resultados.length === 1 ? "" : "s"} para "
                {mutation.data?.query}"
              </span>
            </div>

            {resultados.map((item) => (
              <ResultadoCard key={item.id} item={item} />
            ))}
          </section>
        )}
      </div>
    </main>
  );
}

function ResultadoCard({ item }: { item: ResultadoBusqueda }) {
  const color = colorSimilitud(item.similitud);
  return (
    <article className="rounded-2xl border border-border bg-card p-5 transition-colors hover:border-primary/60">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex-1">
          <p className="text-xs uppercase tracking-widest text-muted-foreground">{item.categoria}</p>
          <h3 className="mt-1 text-lg font-semibold text-foreground">{item.titulo}</h3>
        </div>
        <span
          className="shrink-0 rounded-full px-3 py-1 text-xs font-bold"
          style={{
            backgroundColor: `color-mix(in oklab, ${color} 18%, transparent)`,
            color,
          }}
        >
          {Math.round(item.similitud * 100)}% coincidencia
        </span>
      </div>

      <p className="mt-3 text-sm text-muted-foreground">{item.resumen}</p>

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {item.palabrasClave.map((palabra) => (
          <span
            key={palabra}
            className="rounded-full border border-border bg-secondary px-3 py-1 text-sm"
          >
            #{palabra}
          </span>
        ))}
      </div>

      <div className="mt-4 flex items-center gap-4 text-xs text-muted-foreground">
        {item.autor && <span>{item.autor}</span>}
        <span>{item.fecha}</span>
      </div>

      <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-secondary">
        <div
          className="h-full rounded-full"
          style={{ width: `${item.similitud * 100}%`, backgroundColor: color }}
        />
      </div>
    </article>
  );
}
