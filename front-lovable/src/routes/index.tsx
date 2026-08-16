import { createFileRoute, Link } from "@tanstack/react-router";
import { useServerFn } from "@tanstack/react-start";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";

import logo from "@/assets/honeyguard-logo.png";
import { clasificarContenido } from "@/lib/contenido.functions";

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
  const clasificar = useServerFn(clasificarContenido);
  const mutation = useMutation({
    mutationFn: (valor: string) => clasificar({ data: { texto: valor } }),
  });

  const resultado = mutation.data;

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
          <label htmlFor="contenido" className="text-sm font-medium">
            Contenido a clasificar
          </label>
          <textarea
            id="contenido"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            rows={7}
            placeholder="Pega aquí tu documentación, apunte, tutorial o artículo…"
            className="mt-3 w-full resize-y rounded-xl border border-border bg-background p-4 text-sm text-foreground outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-ring"
          />
          <div className="mt-4 flex items-center justify-between gap-4">
            <span className="text-xs text-muted-foreground">
              {texto.trim().length} caracteres · endpoint /contenido (simulado)
            </span>
            <button
              type="button"
              disabled={!texto.trim() || mutation.isPending}
              onClick={() => mutation.mutate(texto)}
              className="rounded-xl px-6 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity disabled:opacity-40"
              style={{ backgroundImage: "var(--gradient-honey)" }}
            >
              {mutation.isPending ? "Clasificando…" : "Clasificar"}
            </button>
          </div>
          {mutation.isError && (
            <p className="mt-3 text-sm text-destructive">
              No se pudo clasificar el contenido. Intenta de nuevo.
            </p>
          )}
        </section>

        {resultado && (
          <section className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-border bg-card p-6">
              <p className="text-xs uppercase tracking-widest text-muted-foreground">Categoría</p>
              <p className="mt-2 text-2xl font-semibold text-primary">{resultado.categoria}</p>
            </div>

            <div className="rounded-2xl border border-border bg-card p-6">
              <p className="text-xs uppercase tracking-widest text-muted-foreground">
                Probabilidad
              </p>
              <p className="mt-2 text-2xl font-semibold">
                {Math.round(resultado.probabilidad * 100)}%
              </p>
              <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-secondary">
                <div
                  className="h-full rounded-full"
                  style={{
                    width: `${resultado.probabilidad * 100}%`,
                    backgroundImage: "var(--gradient-honey)",
                  }}
                />
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-card p-6 sm:col-span-2">
              <p className="text-xs uppercase tracking-widest text-muted-foreground">
                Palabras clave
              </p>
              <ul className="mt-3 flex flex-wrap gap-2">
                {resultado.palabrasClave.length === 0 && (
                  <li className="text-sm text-muted-foreground">Sin palabras clave relevantes</li>
                )}
                {resultado.palabrasClave.map((palabra) => (
                  <li
                    key={palabra}
                    className="rounded-full border border-border bg-secondary px-3 py-1 text-sm"
                  >
                    #{palabra}
                  </li>
                ))}
              </ul>
              <p className="mt-4 text-sm text-muted-foreground">{resultado.resumen}</p>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
