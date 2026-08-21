import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { buscarContenido } from "@/lib/api";
import { TarjetaDocumento } from "./biblioteca";

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

function BuscarContenidos() {
  const [texto, setTexto] = useState("");
  const [categoria, setCategoria] = useState("");
  const [autor, setAutor] = useState("");
  const [tipo, setTipo] = useState("");
  const [filtros, setFiltros] = useState<null | {
    q: string;
    categoria: string;
    autor: string;
    tipo_contenido: string;
  }>(null);

  const busqueda = useQuery({
    queryKey: ["buscar", filtros],
    queryFn: () => buscarContenido({ ...filtros!, limit: 20 }),
    enabled: filtros !== null,
  });

  function buscar() {
    setFiltros({ q: texto.trim(), categoria, autor, tipo_contenido: tipo });
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex max-w-3xl flex-col gap-8 px-6 py-12">
        <header className="flex flex-col gap-2">
          <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
            ← Volver al inicio
          </Link>
          <h1 className="text-3xl font-bold tracking-tight">Buscar contenidos</h1>
          <p className="text-sm text-muted-foreground">
            Busca por texto libre en el contenido y sus metadatos, o filtra por categoría, autor y
            tipo.
          </p>
        </header>

        <section
          className="flex flex-col gap-3 rounded-2xl border border-border p-5"
          style={{ backgroundColor: "var(--surface-elevated)" }}
        >
          <input
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && buscar()}
            placeholder="Ej.: docker, arquitectura limpia, postgres…"
            className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-ring"
          />

          <div className="grid gap-3 sm:grid-cols-3">
            <input
              value={categoria}
              onChange={(e) => setCategoria(e.target.value)}
              placeholder="Categoría (opcional)"
              className="rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-ring"
            />
            <input
              value={autor}
              onChange={(e) => setAutor(e.target.value)}
              placeholder="Autor (opcional)"
              className="rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-ring"
            />
            <input
              value={tipo}
              onChange={(e) => setTipo(e.target.value)}
              placeholder="Tipo (opcional)"
              className="rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <button
            type="button"
            onClick={buscar}
            disabled={busqueda.isFetching}
            className="rounded-xl px-6 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity disabled:opacity-40"
            style={{ backgroundImage: "var(--gradient-honey)" }}
          >
            {busqueda.isFetching ? "Buscando…" : "Buscar"}
          </button>
        </section>

        {busqueda.isError && (
          <p className="text-sm text-destructive">{(busqueda.error as Error).message}</p>
        )}

        {busqueda.data && (
          <section className="flex flex-col gap-4">
            <p className="text-sm text-muted-foreground">
              {busqueda.data.total} resultado(s)
              {busqueda.data.query ? ` para “${busqueda.data.query}”` : ""}
            </p>
            {busqueda.data.resultados.length === 0 && (
              <p className="rounded-2xl border border-border bg-card p-5 text-sm text-muted-foreground">
                No se encontraron documentos con esos criterios. Prueba con otras palabras o{" "}
                <Link to="/subir" className="text-primary underline-offset-4 hover:underline">
                  sube un archivo nuevo
                </Link>
                .
              </p>
            )}
            {busqueda.data.resultados.map((doc) => (
              <TarjetaDocumento key={doc.id} doc={doc} />
            ))}
          </section>
        )}
      </div>
    </main>
  );
}
