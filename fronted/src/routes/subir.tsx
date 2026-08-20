import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import {
  subirArchivoContenido,
  esRespuestaDuplicado,
  type RespuestaCargaArchivo,
} from "@/lib/contenido-api";

export const Route = createFileRoute("/subir")({
  head: () => ({
    meta: [
      { title: "Subir archivo — HoneyGuard" },
      {
        name: "description",
        content:
          "Sube un PDF o TXT a HoneyGuard: el backend lo clasifica, resume y guarda al instante, devolviendo categoría, probabilidad y palabras clave.",
      },
      { property: "og:title", content: "Subir archivo — HoneyGuard" },
      {
        property: "og:description",
        content:
          "Sube un PDF o TXT a HoneyGuard: el backend lo clasifica, resume y guarda al instante, devolviendo categoría, probabilidad y palabras clave.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SubirArchivo,
});

const TIPOS = ["artículo", "documentación", "tutorial", "apunte", "investigación", "otro"];

function colorConfianza(requiereRevision: boolean, probabilidad: number) {
  if (requiereRevision) return "var(--confianza-baja)";
  if (probabilidad < 0.75) return "var(--confianza-media)";
  return "var(--confianza-alta)";
}

function SubirArchivo() {
  const [archivo, setArchivo] = useState<File | null>(null);
  const [autor, setAutor] = useState("");
  const [tipo, setTipo] = useState("artículo");
  const [errorLocal, setErrorLocal] = useState("");

  const subida = useMutation<RespuestaCargaArchivo, Error>({
    mutationFn: () =>
      subirArchivoContenido({
        file: archivo!,
        autor: autor.trim() || "Desconocido",
        tipo,
      }),
  });

  const resultado = subida.data;
  const duplicado = resultado && esRespuestaDuplicado(resultado) ? resultado : null;
  const exitoso = resultado && !esRespuestaDuplicado(resultado) ? resultado : null;

  function reset() {
    setArchivo(null);
    setAutor("");
    setTipo("artículo");
    setErrorLocal("");
    subida.reset();
  }

  function onFile(file: File | null) {
    setErrorLocal("");
    subida.reset();
    if (!file) return setArchivo(null);
    if (!/\.(pdf|txt)$/i.test(file.name)) {
      setArchivo(null);
      setErrorLocal("Solo se aceptan archivos .pdf o .txt");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setArchivo(null);
      setErrorLocal("El archivo supera los 10 MB");
      return;
    }
    setArchivo(file);
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex max-w-3xl flex-col gap-8 px-6 py-12">
        <header className="flex flex-col gap-2">
          <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
            ← Volver al inicio
          </Link>
          <h1 className="text-3xl font-bold tracking-tight">Subir archivo</h1>
          <p className="text-sm text-muted-foreground">
            Sube un <strong>.pdf</strong> o <strong>.txt</strong>. HoneyGuard lo clasifica, lo
            resume y lo guarda al instante en el backend.
          </p>
        </header>

        {!resultado && (
          <section
            className="rounded-2xl border border-border p-6"
            style={{ backgroundColor: "var(--surface-elevated)" }}
          >
            <label
              htmlFor="archivo"
              className="flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed border-border px-6 py-10 text-center transition-colors hover:border-primary"
            >
              <span className="text-sm font-medium">
                {archivo ? archivo.name : "Selecciona o arrastra tu archivo"}
              </span>
              <span className="text-xs text-muted-foreground">
                {archivo
                  ? `${(archivo.size / 1024).toFixed(0)} KB`
                  : "Formatos aceptados: PDF y TXT (máx. 10 MB)"}
              </span>
              <input
                id="archivo"
                type="file"
                accept=".pdf,.txt,application/pdf,text/plain"
                className="sr-only"
                onChange={(e) => onFile(e.target.files?.[0] ?? null)}
              />
            </label>

            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-2">
                <label
                  htmlFor="autor"
                  className="text-xs uppercase tracking-widest text-muted-foreground"
                >
                  Autor (opcional)
                </label>
                <input
                  id="autor"
                  type="text"
                  value={autor}
                  onChange={(e) => setAutor(e.target.value)}
                  placeholder="Desconocido"
                  className="rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div className="flex flex-col gap-2">
                <label
                  htmlFor="tipo"
                  className="text-xs uppercase tracking-widest text-muted-foreground"
                >
                  Tipo
                </label>
                <select
                  id="tipo"
                  value={tipo}
                  onChange={(e) => setTipo(e.target.value)}
                  className="rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-ring"
                >
                  {TIPOS.map((t) => (
                    <option key={t} value={t}>
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {errorLocal && <p className="mt-3 text-sm text-destructive">{errorLocal}</p>}
            {subida.isError && (
              <p className="mt-3 text-sm text-destructive">
                {subida.error.message || "No se pudo subir el archivo."}
              </p>
            )}

            <button
              type="button"
              disabled={!archivo || subida.isPending}
              onClick={() => subida.mutate()}
              className="mt-4 w-full rounded-xl px-6 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity disabled:opacity-40"
              style={{ backgroundImage: "var(--gradient-honey)" }}
            >
              {subida.isPending ? "Subiendo y clasificando…" : "Subir y clasificar"}
            </button>
            <p className="mt-2 text-center text-xs text-muted-foreground">
              El backend en Render tarda unos segundos la primera vez (cold start).
            </p>
          </section>
        )}

        {duplicado && (
          <section className="flex flex-col gap-4">
            <div
              className="flex items-center gap-3 rounded-2xl border p-5"
              style={{
                borderColor: "var(--confianza-media)",
                backgroundColor: "color-mix(in oklab, var(--confianza-media) 12%, transparent)",
              }}
            >
              <span className="text-2xl" aria-hidden>
                ⚠️
              </span>
              <div className="flex flex-col">
                <span className="text-sm font-semibold" style={{ color: "var(--confianza-media)" }}>
                  Documento duplicado
                </span>
                <span className="text-xs text-muted-foreground">{duplicado.mensaje}</span>
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-card p-5">
              <p className="text-xs uppercase tracking-widest text-muted-foreground">
                Documento original
              </p>
              <p className="mt-1 text-lg font-semibold text-primary">
                {duplicado.documento_original.titulo ??
                  `Documento #${duplicado.documento_original.id}`}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                ID {duplicado.documento_original.id} · {Math.round(duplicado.similitud * 100)}% de
                similitud con el archivo que subiste
              </p>
            </div>

            <button
              type="button"
              onClick={reset}
              className="self-start rounded-xl border border-border px-4 py-2 text-sm font-medium transition-colors hover:bg-secondary"
            >
              Subir otro archivo
            </button>
          </section>
        )}

        {exitoso && (
          <section className="flex flex-col gap-4">
            <div
              className="flex items-center gap-3 rounded-2xl border p-5"
              style={{
                borderColor: colorConfianza(
                  exitoso.clasificacion.requiere_revision,
                  exitoso.clasificacion.probabilidad,
                ),
                backgroundColor: `color-mix(in oklab, ${colorConfianza(
                  exitoso.clasificacion.requiere_revision,
                  exitoso.clasificacion.probabilidad,
                )} 12%, transparent)`,
              }}
            >
              <span className="text-2xl" aria-hidden>
                {exitoso.clasificacion.requiere_revision ? "🔎" : "✅"}
              </span>
              <div className="flex flex-col">
                <span
                  className="text-sm font-semibold"
                  style={{
                    color: colorConfianza(
                      exitoso.clasificacion.requiere_revision,
                      exitoso.clasificacion.probabilidad,
                    ),
                  }}
                >
                  {exitoso.clasificacion.requiere_revision
                    ? "Contenido guardado — confianza baja, revisar categoría"
                    : "Contenido guardado"}
                </span>
                <span className="text-xs text-muted-foreground">ID {exitoso.metadatos.id}</span>
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-card p-5">
              <div className="grid gap-4">
                <div>
                  <p className="text-xs uppercase tracking-widest text-muted-foreground">
                    Categoría
                  </p>
                  <p className="mt-1 text-lg font-semibold text-primary">
                    {exitoso.clasificacion.categoria}
                  </p>
                </div>

                <div>
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-xs uppercase tracking-widest text-muted-foreground">
                      Probabilidad
                    </p>
                    <span className="text-sm font-semibold">
                      {Math.round(exitoso.clasificacion.probabilidad * 100)}%
                    </span>
                  </div>
                  <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-secondary">
                    <div
                      className="h-full rounded-full"
                      style={{
                        width: `${exitoso.clasificacion.probabilidad * 100}%`,
                        backgroundImage: "var(--gradient-honey)",
                      }}
                    />
                  </div>
                </div>

                <div>
                  <p className="text-xs uppercase tracking-widest text-muted-foreground">
                    Palabras clave
                  </p>
                  <ul className="mt-2 flex flex-wrap gap-2">
                    {exitoso.clasificacion.palabras_clave.length === 0 && (
                      <li className="text-sm text-muted-foreground">Sin palabras clave</li>
                    )}
                    {exitoso.clasificacion.palabras_clave.map((p) => (
                      <li
                        key={p}
                        className="rounded-full border border-border bg-secondary px-3 py-1 text-sm"
                      >
                        #{p}
                      </li>
                    ))}
                  </ul>
                </div>

                <div>
                  <p className="text-xs uppercase tracking-widest text-muted-foreground">
                    Resumen automático
                  </p>
                  <p className="mt-2 text-sm text-foreground whitespace-pre-line">
                    {exitoso.clasificacion.resumen || "Sin resumen disponible."}
                  </p>
                </div>

                {exitoso.contenido_relacionado.length > 0 && (
                  <div>
                    <p className="text-xs uppercase tracking-widest text-muted-foreground">
                      Documentos relacionados
                    </p>
                    <ul className="mt-2 flex flex-col gap-1.5">
                      {exitoso.contenido_relacionado.map((doc) => (
                        <li
                          key={doc.id}
                          className="flex items-center justify-between gap-3 rounded-lg border border-border px-3 py-2 text-sm"
                        >
                          <span className="truncate">{doc.titulo ?? `Documento #${doc.id}`}</span>
                          <span className="shrink-0 text-xs text-muted-foreground">
                            {Math.round(doc.similitud * 100)}% similar
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-muted-foreground">
                  <span>
                    Autor:{" "}
                    <strong className="text-foreground">
                      {exitoso.metadatos.autor ?? "Desconocido"}
                    </strong>
                  </span>
                  <span>
                    Tipo:{" "}
                    <strong className="text-foreground">
                      {exitoso.metadatos.tipo_contenido ?? "—"}
                    </strong>
                  </span>
                </div>

                {exitoso.metadatos.url_archivo && (
                  <a
                    href={exitoso.metadatos.url_archivo}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="self-start text-sm font-medium text-primary underline-offset-4 hover:underline"
                  >
                    Ver archivo original ↗
                  </a>
                )}
              </div>
            </div>

            <button
              type="button"
              onClick={reset}
              className="self-start rounded-xl border border-border px-4 py-2 text-sm font-medium transition-colors hover:bg-secondary"
            >
              Subir otro archivo
            </button>
          </section>
        )}
      </div>
    </main>
  );
}
