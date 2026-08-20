import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import {
  buscarContenido,
  listarContenido,
  obtenerContenidoPorId,
  type DocumentoCompleto,
  type DocumentoListado,
  type RespuestaBusqueda,
  type RespuestaListaDocumentos,
} from "@/lib/contenido-api";

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

function DocumentoCard({
  documento,
  onDetalle,
  cargando,
}: {
  documento: DocumentoListado;
  onDetalle: (id: number) => void;
  cargando: boolean;
}) {
  return (
    <article className="rounded-2xl border border-border bg-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-widest text-muted-foreground">
            {documento.tipo_contenido || documento.formato_archivo}
          </p>
          <h2 className="mt-1 text-lg font-semibold text-foreground">
            {documento.titulo || `Documento #${documento.id}`}
          </h2>
          <p className="mt-1 text-xs text-muted-foreground">
            ID {documento.id} · {documento.autor || "Autor desconocido"}
          </p>
        </div>
        <span className="rounded-full border border-border bg-secondary px-3 py-1 text-xs font-medium text-primary">
          {documento.categoria}
        </span>
      </div>

      {documento.resumen && (
        <p className="mt-4 line-clamp-4 text-sm leading-6 text-muted-foreground">
          {documento.resumen}
        </p>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {(documento.palabras_clave || []).slice(0, 6).map((palabra) => (
          <span key={palabra} className="rounded-full bg-secondary px-2.5 py-1 text-xs">
            #{palabra}
          </span>
        ))}
      </div>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
        <span className="text-xs text-muted-foreground">
          Confianza: {Math.round(documento.probabilidad * 100)}%
        </span>
        <button
          type="button"
          onClick={() => onDetalle(documento.id)}
          disabled={cargando}
          className="rounded-xl border border-border px-4 py-2 text-sm font-medium hover:border-primary disabled:opacity-40"
        >
          Ver documento completo
        </button>
      </div>
    </article>
  );
}

function DetalleDocumento({ documento, onCerrar }: { documento: DocumentoCompleto; onCerrar: () => void }) {
  return (
    <section className="rounded-2xl border border-primary/40 bg-card p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-widest text-muted-foreground">Documento completo</p>
          <h2 className="mt-1 text-2xl font-bold">
            {documento.titulo || `Documento #${documento.id}`}
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {documento.autor || "Autor desconocido"} · {documento.categoria} · {Math.round(documento.probabilidad * 100)}%
          </p>
        </div>
        <button
          type="button"
          onClick={onCerrar}
          className="rounded-xl border border-border px-3 py-1.5 text-sm hover:border-primary"
        >
          Cerrar
        </button>
      </div>

      {documento.resumen && (
        <div className="mt-5">
          <p className="text-xs uppercase tracking-widest text-muted-foreground">Resumen</p>
          <p className="mt-2 text-sm leading-6">{documento.resumen}</p>
        </div>
      )}

      <div className="mt-5">
        <p className="text-xs uppercase tracking-widest text-muted-foreground">Contenido</p>
        <div className="mt-2 max-h-96 overflow-y-auto whitespace-pre-wrap rounded-xl border border-border bg-background p-4 text-sm leading-6">
          {documento.texto}
        </div>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        {(documento.palabras_clave || []).map((palabra) => (
          <span key={palabra} className="rounded-full bg-secondary px-3 py-1 text-xs">
            #{palabra}
          </span>
        ))}
      </div>
    </section>
  );
}

function BuscarContenidos() {
  const [q, setQ] = useState("");
  const [categoria, setCategoria] = useState("");
  const [autor, setAutor] = useState("");
  const [tipoContenido, setTipoContenido] = useState("");
  const [resultados, setResultados] = useState<DocumentoListado[]>([]);
  const [total, setTotal] = useState<number | null>(null);
  const [detalle, setDetalle] = useState<DocumentoCompleto | null>(null);

  const busqueda = useMutation<RespuestaBusqueda, Error>({
    mutationFn: () =>
      buscarContenido(q.trim(), {
        categoria: categoria.trim() || undefined,
        autor: autor.trim() || undefined,
        tipo_contenido: tipoContenido.trim() || undefined,
        limit: 50,
      }),
    onSuccess: (data) => {
      setResultados(data.resultados);
      setTotal(data.total);
      setDetalle(null);
    },
  });

  const listado = useMutation<RespuestaListaDocumentos, Error>({
    mutationFn: () =>
      listarContenido({
        categoria: categoria.trim() || undefined,
        autor: autor.trim() || undefined,
        tipo_contenido: tipoContenido.trim() || undefined,
        limit: 50,
      }),
    onSuccess: (data) => {
      setResultados(data.items);
      setTotal(data.total);
      setDetalle(null);
    },
  });

  const consulta = useMutation<DocumentoCompleto, Error, number>({
  mutationFn: (id: number) => obtenerContenidoPorId(id),
  onSuccess: (data) => setDetalle(data),
});

  const cargando = busqueda.isPending || listado.isPending;
  const error = busqueda.error || listado.error || consulta.error;

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex max-w-4xl flex-col gap-8 px-6 py-12">
        <header className="flex flex-col gap-2">
          <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
            ← Volver al inicio
          </Link>
          <h1 className="text-3xl font-bold tracking-tight">Buscar contenidos</h1>
          <p className="text-sm text-muted-foreground">
            Consulta directamente los documentos almacenados en Oracle y abre el contenido completo por ID.
          </p>
        </header>

        <section
          className="rounded-2xl border border-border p-6"
          style={{ backgroundColor: "var(--surface-elevated)" }}
        >
          <div className="grid gap-4">
            <div>
              <label htmlFor="q" className="text-sm font-medium">Texto de búsqueda</label>
              <input
                id="q"
                value={q}
                onChange={(event) => setQ(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") busqueda.mutate();
                }}
                placeholder="Ej. Oracle, FastAPI, seguridad, redes…"
                className="mt-2 w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:border-primary"
              />
            </div>

            <div className="grid gap-3 md:grid-cols-3">
              <input
                value={categoria}
                onChange={(event) => setCategoria(event.target.value)}
                placeholder="Filtrar por categoría"
                className="rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:border-primary"
              />
              <input
                value={autor}
                onChange={(event) => setAutor(event.target.value)}
                placeholder="Filtrar por autor"
                className="rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:border-primary"
              />
              <input
                value={tipoContenido}
                onChange={(event) => setTipoContenido(event.target.value)}
                placeholder="Tipo de contenido"
                className="rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:border-primary"
              />
            </div>

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => busqueda.mutate()}
                disabled={cargando}
                className="rounded-xl px-5 py-2.5 text-sm font-semibold text-primary-foreground disabled:opacity-40"
                style={{ backgroundImage: "var(--gradient-honey)" }}
              >
                {busqueda.isPending ? "Buscando…" : "Buscar"}
              </button>
              <button
                type="button"
                onClick={() => listado.mutate()}
                disabled={cargando}
                className="rounded-xl border border-border px-5 py-2.5 text-sm font-medium hover:border-primary disabled:opacity-40"
              >
                {listado.isPending ? "Cargando…" : "Listar todos"}
              </button>
              <Link
                to="/subir"
                className="rounded-xl border border-border px-5 py-2.5 text-sm font-medium hover:border-primary"
              >
                Subir nuevo archivo
              </Link>
            </div>
          </div>

          {error && <p className="mt-4 text-sm text-destructive">{error.message}</p>}
        </section>

        {detalle && <DetalleDocumento documento={detalle} onCerrar={() => setDetalle(null)} />}

        {total !== null && (
          <section className="flex flex-col gap-4">
            <div className="flex items-center justify-between gap-3">
              <h2 className="text-lg font-semibold">Resultados</h2>
              <span className="text-sm text-muted-foreground">{total} documento(s)</span>
            </div>

            {resultados.length === 0 ? (
              <div className="rounded-2xl border border-border bg-card p-6 text-sm text-muted-foreground">
                No se encontraron documentos con esos criterios.
              </div>
            ) : (
              resultados.map((documento) => (
                <DocumentoCard
                  key={documento.id}
                  documento={documento}
                  onDetalle={(id) => consulta.mutate(id)}
                  cargando={consulta.isPending}
                />
              ))
            )}
          </section>
        )}
      </div>
    </main>
  );
}
