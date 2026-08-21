import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { listarContenido, colorConfianza, porcentaje, type Documento } from "@/lib/api";

export const Route = createFileRoute("/biblioteca")({
  head: () => ({
    meta: [
      { title: "Biblioteca — HoneyGuard" },
      {
        name: "description",
        content:
          "Explora todos los documentos guardados en HoneyGuard, filtrados por categoría, autor o tipo de contenido.",
      },
      { property: "og:title", content: "Biblioteca — HoneyGuard" },
      {
        property: "og:description",
        content:
          "Explora todos los documentos guardados en HoneyGuard, filtrados por categoría, autor o tipo de contenido.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Biblioteca,
});

const LIMITE = 20;

function Biblioteca() {
  const [categoria, setCategoria] = useState("");
  const [autor, setAutor] = useState("");
  const [tipo, setTipo] = useState("");
  const [offset, setOffset] = useState(0);
  const [filtros, setFiltros] = useState({ categoria: "", autor: "", tipo_contenido: "" });

  const lista = useQuery({
    queryKey: ["biblioteca", filtros, offset],
    queryFn: () => listarContenido({ ...filtros, offset, limit: LIMITE }),
  });

  function aplicar() {
    setOffset(0);
    setFiltros({ categoria, autor, tipo_contenido: tipo });
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex max-w-3xl flex-col gap-8 px-6 py-12">
        <header className="flex flex-col gap-2">
          <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
            ← Volver al inicio
          </Link>
          <h1 className="text-3xl font-bold tracking-tight">Biblioteca</h1>
          <p className="text-sm text-muted-foreground">
            Todos los documentos guardados en el backend, con sus metadatos y clasificación.
          </p>
        </header>

        <section
          className="grid gap-3 rounded-2xl border border-border p-5 sm:grid-cols-3"
          style={{ backgroundColor: "var(--surface-elevated)" }}
        >
          <input
            value={categoria}
            onChange={(e) => setCategoria(e.target.value)}
            placeholder="Categoría"
            className="rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-ring"
          />
          <input
            value={autor}
            onChange={(e) => setAutor(e.target.value)}
            placeholder="Autor"
            className="rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-ring"
          />
          <input
            value={tipo}
            onChange={(e) => setTipo(e.target.value)}
            placeholder="Tipo de contenido"
            className="rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-ring"
          />
          <button
            type="button"
            onClick={aplicar}
            className="rounded-xl px-5 py-2.5 text-sm font-semibold text-primary-foreground sm:col-span-3"
            style={{ backgroundImage: "var(--gradient-honey)" }}
          >
            Aplicar filtros
          </button>
        </section>

        {lista.isPending && <p className="text-sm text-muted-foreground">Cargando documentos…</p>}
        {lista.isError && (
          <p className="text-sm text-destructive">{(lista.error as Error).message}</p>
        )}

        {lista.data && (
          <section className="flex flex-col gap-4">
            <p className="text-sm text-muted-foreground">
              {lista.data.total} documento(s) — mostrando {lista.data.items.length}
            </p>
            {lista.data.items.map((doc) => (
              <TarjetaDocumento key={doc.id} doc={doc} />
            ))}

            <div className="flex items-center justify-between gap-3">
              <button
                type="button"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - LIMITE))}
                className="rounded-xl border border-border px-4 py-2 text-sm disabled:opacity-40"
              >
                ← Anteriores
              </button>
              <button
                type="button"
                disabled={offset + LIMITE >= lista.data.total}
                onClick={() => setOffset(offset + LIMITE)}
                className="rounded-xl border border-border px-4 py-2 text-sm disabled:opacity-40"
              >
                Siguientes →
              </button>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

export function TarjetaDocumento({ doc }: { doc: Documento }) {
  return (
    <article className="rounded-2xl border border-border bg-card p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold">
            {doc.titulo?.trim() || `Documento #${doc.id}`}
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            {doc.categoria}
            {doc.autor ? ` · ${doc.autor}` : ""}
            {doc.tipo_contenido ? ` · ${doc.tipo_contenido}` : ""} ·{" "}
            {doc.formato_archivo.toUpperCase()} ·{" "}
            {new Date(doc.fecha_creacion).toLocaleDateString("es")}
          </p>
        </div>
        <span
          className="shrink-0 rounded-full border px-3 py-1 text-xs font-semibold"
          style={{ borderColor: colorConfianza(doc.probabilidad), color: colorConfianza(doc.probabilidad) }}
        >
          {porcentaje(doc.probabilidad)}%
        </span>
      </div>

      {doc.resumen && (
        <p className="mt-3 text-sm text-muted-foreground whitespace-pre-line">{doc.resumen}</p>
      )}

      {doc.palabras_clave && doc.palabras_clave.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-2">
          {doc.palabras_clave.map((p) => (
            <li key={p} className="rounded-full border border-border bg-secondary px-3 py-1 text-xs">
              #{p}
            </li>
          ))}
        </ul>
      )}

      <div className="mt-4 flex flex-wrap gap-4 text-sm">
        <Link
          to="/documento/$id"
          params={{ id: String(doc.id) }}
          className="font-medium text-primary underline-offset-4 hover:underline"
        >
          Ver detalle →
        </Link>
        <a
          href={doc.url_archivo}
          target="_blank"
          rel="noopener noreferrer"
          className="text-muted-foreground underline-offset-4 hover:underline"
        >
          Archivo original ↗
        </a>
      </div>
    </article>
  );
}
