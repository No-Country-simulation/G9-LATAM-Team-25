import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";

import { obtenerContenido, colorConfianza, porcentaje } from "@/lib/api";

export const Route = createFileRoute("/documento/$id")({
  head: () => ({
    meta: [
      { title: "Detalle del documento — HoneyGuard" },
      {
        name: "description",
        content:
          "Consulta la categoría, el resumen, las palabras clave y el texto extraído de un documento guardado en HoneyGuard.",
      },
      { property: "og:title", content: "Detalle del documento — HoneyGuard" },
      {
        property: "og:description",
        content:
          "Consulta la categoría, el resumen, las palabras clave y el texto extraído de un documento guardado en HoneyGuard.",
      },
      { property: "og:type", content: "article" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: DetalleDocumento,
});

function DetalleDocumento() {
  const { id } = Route.useParams();

  const doc = useQuery({
    queryKey: ["documento", id],
    queryFn: () => obtenerContenido(id),
  });

  const d = doc.data;

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex max-w-3xl flex-col gap-8 px-6 py-12">
        <header className="flex flex-col gap-2">
          <Link to="/biblioteca" className="text-sm text-muted-foreground hover:text-foreground">
            ← Volver a la biblioteca
          </Link>
          <h1 className="text-3xl font-bold tracking-tight">
            {d?.titulo?.trim() || `Documento #${id}`}
          </h1>
        </header>

        {doc.isPending && <p className="text-sm text-muted-foreground">Cargando documento…</p>}
        {doc.isError && <p className="text-sm text-destructive">{(doc.error as Error).message}</p>}

        {d && (
          <section className="flex flex-col gap-4">
            <div className="rounded-2xl border border-border bg-card p-5">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-widest text-muted-foreground">
                    Categoría
                  </p>
                  <p className="mt-1 text-lg font-semibold text-primary">{d.categoria}</p>
                </div>
                <span
                  className="rounded-full border px-3 py-1 text-sm font-semibold"
                  style={{ borderColor: colorConfianza(d.probabilidad), color: colorConfianza(d.probabilidad) }}
                >
                  {porcentaje(d.probabilidad)}%
                </span>
              </div>

              <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-xs text-muted-foreground">
                {d.autor && (
                  <span>
                    Autor: <strong className="text-foreground">{d.autor}</strong>
                  </span>
                )}
                {d.tema && (
                  <span>
                    Tema: <strong className="text-foreground">{d.tema}</strong>
                  </span>
                )}
                {d.tipo_contenido && (
                  <span>
                    Tipo: <strong className="text-foreground">{d.tipo_contenido}</strong>
                  </span>
                )}
                <span>
                  Formato: <strong className="text-foreground">{d.formato_archivo.toUpperCase()}</strong>
                </span>
                <span>
                  Fecha:{" "}
                  <strong className="text-foreground">
                    {new Date(d.fecha_creacion).toLocaleDateString("es")}
                  </strong>
                </span>
              </div>

              {d.resumen && (
                <div className="mt-4">
                  <p className="text-xs uppercase tracking-widest text-muted-foreground">Resumen</p>
                  <p className="mt-2 text-sm whitespace-pre-line">{d.resumen}</p>
                </div>
              )}

              {d.palabras_clave && d.palabras_clave.length > 0 && (
                <ul className="mt-4 flex flex-wrap gap-2">
                  {d.palabras_clave.map((p) => (
                    <li
                      key={p}
                      className="rounded-full border border-border bg-secondary px-3 py-1 text-xs"
                    >
                      #{p}
                    </li>
                  ))}
                </ul>
              )}

              <a
                href={d.url_archivo}
                target="_blank"
                rel="noopener noreferrer"
                className="mt-4 inline-block text-sm font-medium text-primary underline-offset-4 hover:underline"
              >
                Ver archivo original ↗
              </a>
            </div>

            {d.contenido_relacionado && d.contenido_relacionado.length > 0 && (
              <div className="rounded-2xl border border-border bg-card p-5">
                <p className="text-xs uppercase tracking-widest text-muted-foreground">
                  Contenido relacionado
                </p>
                <ul className="mt-2 flex flex-wrap gap-3 text-sm">
                  {d.contenido_relacionado.map((rid) => (
                    <li key={rid}>
                      <Link
                        to="/documento/$id"
                        params={{ id: String(rid) }}
                        className="text-primary underline-offset-4 hover:underline"
                      >
                        Documento #{rid}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <details className="rounded-2xl border border-border bg-card p-5">
              <summary className="cursor-pointer text-sm font-semibold">Texto extraído</summary>
              <p className="mt-3 text-sm text-muted-foreground whitespace-pre-line">{d.texto}</p>
            </details>
          </section>
        )}
      </div>
    </main>
  );
}
