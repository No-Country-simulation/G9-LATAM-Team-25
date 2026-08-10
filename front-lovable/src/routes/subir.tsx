import { createFileRoute, Link } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import {
  analizarArchivo,
  guardarContenido,
  type CampoExtraido,
  type DuplicadoDetectado,
} from "@/lib/archivos.functions";

export const Route = createFileRoute("/subir")({
  head: () => ({
    meta: [
      { title: "Subir archivo — HoneyGuard" },
      {
        name: "description",
        content:
          "Sube un PDF o TXT a HoneyGuard: extrae los campos automáticamente, revisa su nivel de confianza, corrígelos y guárdalos.",
      },
      { property: "og:title", content: "Subir archivo — HoneyGuard" },
      {
        property: "og:description",
        content:
          "Sube un PDF o TXT a HoneyGuard: extrae los campos automáticamente, revisa su nivel de confianza, corrígelos y guárdalos.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: SubirArchivo,
});

function nivel(confianza: number) {
  if (confianza >= 0.75) return { texto: "Alta confianza", color: "var(--confianza-alta)" };
  if (confianza >= 0.5) return { texto: "Confianza media", color: "var(--confianza-media)" };
  return { texto: "Baja confianza — revisa", color: "var(--confianza-baja)" };
}

function SubirArchivo() {
  const [archivo, setArchivo] = useState<File | null>(null);
  const [campos, setCampos] = useState<CampoExtraido[] | null>(null);
  const [nombreArchivo, setNombreArchivo] = useState("");
  const [duplicado, setDuplicado] = useState<DuplicadoDetectado | null>(null);
  const [errorLocal, setErrorLocal] = useState("");

  const analizar = useServerFn(analizarArchivo);
  const guardar = useServerFn(guardarContenido);

  const analisis = useMutation({
    mutationFn: async (file: File) => {
      const esTxt = /\.txt$/i.test(file.name);
      const texto = esTxt ? (await file.text()).slice(0, 20000) : "";
      return analizar({
        data: { nombre: file.name, tipo: file.type, tamano: file.size, texto },
      });
    },
    onSuccess: (data) => {
      setNombreArchivo(data.archivo);
      if (data.duplicado) {
        setDuplicado(data.duplicado);
        setCampos(null);
      } else {
        setDuplicado(null);
        setCampos(data.campos);
      }
    },
  });

  const guardado = useMutation({
    mutationFn: () =>
      guardar({
        data: {
          archivo: nombreArchivo,
          campos: Object.fromEntries((campos ?? []).map((c) => [c.clave, c.valor])),
        },
      }),
    onSuccess: (data) => {
      if (!data.ok) {
        setDuplicado(data.duplicado);
        setCampos(null);
      }
    },
  });

  function resetArchivo() {
    setArchivo(null);
    setCampos(null);
    setDuplicado(null);
    setNombreArchivo("");
    setErrorLocal("");
    guardado.reset();
    analisis.reset();
  }

  function onFile(file: File | null) {
    setErrorLocal("");
    guardado.reset();
    setCampos(null);
    setDuplicado(null);
    if (!file) return setArchivo(null);
    if (!/\.(pdf|txt)$/i.test(file.name)) {
      setArchivo(null);
      setErrorLocal("Solo se aceptan archivos .pdf o .txt");
      return;
    }
    setArchivo(file);
  }

  function editar(clave: string, valor: string) {
    guardado.reset();
    setCampos((prev) => prev?.map((c) => (c.clave === clave ? { ...c, valor } : c)) ?? prev);
  }

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex max-w-3xl flex-col gap-8 px-6 py-12">
        <header className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">
              ← Volver a clasificar texto
            </Link>
            <span className="text-xs text-muted-foreground">·</span>
            <Link to="/buscar" className="text-sm text-muted-foreground hover:text-foreground">
              Buscar contenidos →
            </Link>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Subir archivo</h1>
          <p className="text-sm text-muted-foreground">
            Sube un <strong>.pdf</strong> o <strong>.txt</strong>. HoneyGuard autocompleta los
            campos; revisa el indicador de confianza, corrige lo que haga falta y confirma.
          </p>
        </header>

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

          {errorLocal && <p className="mt-3 text-sm text-destructive">{errorLocal}</p>}
          {analisis.isError && (
            <p className="mt-3 text-sm text-destructive">
              {(analisis.error as Error).message || "No se pudo analizar el archivo."}
            </p>
          )}

          <button
            type="button"
            disabled={!archivo || analisis.isPending || duplicado !== null}
            onClick={() => archivo && analisis.mutate(archivo)}
            className="mt-4 w-full rounded-xl px-6 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity disabled:opacity-40"
            style={{ backgroundImage: "var(--gradient-honey)" }}
          >
            {analisis.isPending ? "Analizando archivo…" : "Analizar archivo"}
          </button>
        </section>

        {duplicado && (
          <section className="flex flex-col gap-4">
            <div className="rounded-2xl border border-destructive bg-destructive/10 p-6">
              <div className="flex items-start gap-3">
                <span className="text-2xl" aria-hidden>
                  ⚠️
                </span>
                <div className="flex flex-col gap-3">
                  <h2 className="text-lg font-semibold text-destructive-foreground">
                    Carga no realizada
                  </h2>
                  <p className="text-sm text-foreground">
                    La carga no se realizó porque ya existe un documento muy similar.
                  </p>
                  <div className="rounded-xl border border-border bg-background p-4">
                    <p className="text-xs text-muted-foreground">Documento existente</p>
                    <p className="mt-1 text-base font-semibold">{duplicado.titulo}</p>
                    <div className="mt-3 flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">Coincidencia</span>
                      <span
                        className="rounded-full px-2.5 py-0.5 text-sm font-bold"
                        style={{
                          backgroundColor: "color-mix(in oklab, var(--destructive) 20%, transparent)",
                          color: "var(--destructive)",
                        }}
                      >
                        {Math.round(duplicado.similitud * 100)}%
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Para continuar debes subir un archivo distinto.
                  </p>
                  <button
                    type="button"
                    onClick={resetArchivo}
                    className="self-start rounded-xl border border-border px-4 py-2 text-sm font-medium transition-colors hover:bg-secondary"
                  >
                    Subir otro archivo
                  </button>
                </div>
              </div>
            </div>
          </section>
        )}

        {campos && !duplicado && (
          <section className="flex flex-col gap-4">
            {(() => {
              const campoResumen = campos.find((c) => c.clave === "resumen");
              const categoriaValor = campos.find((c) => c.clave === "categoria")?.valor ?? "—";
              const palabrasClaveValor = campos.find((c) => c.clave === "palabrasClave")?.valor ?? "";
              const camposEditables = campos.filter((c) => c.clave !== "resumen");
              const tags = palabrasClaveValor
                .split(",")
                .map((p) => p.trim())
                .filter(Boolean);

              return (
                <>
                  <div className="rounded-2xl border border-border bg-card p-5">
                    <div className="grid gap-4">
                      <div>
                        <p className="text-xs uppercase tracking-widest text-muted-foreground">
                          Categoría
                        </p>
                        <p className="mt-1 text-lg font-semibold text-primary">{categoriaValor}</p>
                      </div>

                      <div>
                        <p className="text-xs uppercase tracking-widest text-muted-foreground">
                          Palabras clave
                        </p>
                        <ul className="mt-2 flex flex-wrap gap-2">
                          {tags.length === 0 && (
                            <li className="text-sm text-muted-foreground">Sin palabras clave</li>
                          )}
                          {tags.map((p) => (
                            <li
                              key={p}
                              className="rounded-full border border-border bg-secondary px-3 py-1 text-sm"
                            >
                              #{p}
                            </li>
                          ))}
                        </ul>
                      </div>

                      {campoResumen && (
                        <div>
                          <div className="flex items-center justify-between gap-2">
                            <label
                              htmlFor={campoResumen.clave}
                              className="text-xs uppercase tracking-widest text-muted-foreground"
                            >
                              Resumen automático
                            </label>
                            <span
                              className="flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium"
                              style={{
                                backgroundColor: `color-mix(in oklab, ${nivel(campoResumen.confianza).color} 18%, transparent)`,
                                color: nivel(campoResumen.confianza).color,
                              }}
                            >
                              <span
                                className="h-2 w-2 rounded-full"
                                style={{ backgroundColor: nivel(campoResumen.confianza).color }}
                                aria-hidden
                              />
                              {Math.round(campoResumen.confianza * 100)}% ·{" "}
                              {nivel(campoResumen.confianza).texto}
                            </span>
                          </div>
                          <textarea
                            id={campoResumen.clave}
                            rows={3}
                            value={campoResumen.valor}
                            onChange={(e) => editar(campoResumen.clave, e.target.value)}
                            className="mt-3 w-full resize-none rounded-xl border border-border bg-background p-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                          />
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-baseline justify-between gap-4">
                    <h2 className="text-xl font-semibold">Revisar campos</h2>
                    <span className="text-xs text-muted-foreground">{nombreArchivo}</span>
                  </div>

                  {camposEditables.map((campo) => {
                    const n = nivel(campo.confianza);
                    return (
                      <div key={campo.clave} className="rounded-2xl border border-border bg-card p-5">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <label htmlFor={campo.clave} className="text-sm font-medium">
                            {campo.etiqueta}
                          </label>
                          <span
                            className="flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium"
                            style={{
                              backgroundColor: `color-mix(in oklab, ${n.color} 18%, transparent)`,
                              color: n.color,
                            }}
                          >
                            <span
                              className="h-2 w-2 rounded-full"
                              style={{ backgroundColor: n.color }}
                              aria-hidden
                            />
                            {Math.round(campo.confianza * 100)}% · {n.texto}
                          </span>
                        </div>

                        <input
                          id={campo.clave}
                          value={campo.valor}
                          onChange={(e) => editar(campo.clave, e.target.value)}
                          className="mt-3 w-full rounded-xl border border-border bg-background p-3 text-sm outline-none focus:ring-2 focus:ring-ring"
                        />

                        <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-secondary">
                          <div
                            className="h-full rounded-full"
                            style={{ width: `${campo.confianza * 100}%`, backgroundColor: n.color }}
                          />
                        </div>
                      </div>
                    );
                  })}

                  <div
                    className="flex flex-col gap-3 rounded-2xl border border-border p-5"
                    style={{ backgroundColor: "var(--surface-elevated)" }}
                  >
                    <p className="text-xs text-muted-foreground">
                      Nada se guarda hasta que confirmes. Edita los campos que necesites y luego pulsa
                      confirmar.
                    </p>
                    <button
                      type="button"
                      disabled={guardado.isPending || (guardado.isSuccess && guardado.data?.ok === true)}
                      onClick={() => guardado.mutate()}
                      className="rounded-xl px-6 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity disabled:opacity-40"
                      style={{ backgroundImage: "var(--gradient-honey)" }}
                    >
                      {guardado.isPending
                        ? "Guardando…"
                        : guardado.isSuccess && guardado.data?.ok
                          ? "Guardado ✓"
                          : "Confirmar y guardar"}
                    </button>
                    {guardado.isError && (
                      <p className="text-sm text-destructive">
                        {(guardado.error as Error).message || "No se pudo guardar."}
                      </p>
                    )}
                    {guardado.isSuccess && guardado.data?.ok && (
                      <>
                        <p className="text-sm" style={{ color: "var(--confianza-alta)" }}>
                          Contenido guardado con id {guardado.data.id}.
                        </p>
                        <button
                          type="button"
                          onClick={resetArchivo}
                          className="self-start rounded-xl border border-border px-4 py-2 text-sm font-medium transition-colors hover:bg-secondary"
                        >
                          Subir otro archivo
                        </button>
                      </>
                    )}
                  </div>
                </>
              );
            })()}
          </section>
        )}
      </div>
    </main>
  );
}
