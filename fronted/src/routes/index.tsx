import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import logo from "@/assets/honeyguard-logo.png";
import { clasificarTexto, colorConfianza, porcentaje } from "@/lib/api";

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
  const { t } = useTranslation();
  const [texto, setTexto] = useState("");

  const clasificacion = useMutation({
    mutationFn: () => clasificarTexto(texto.trim()),
  });

  const resultado = clasificacion.data;

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex max-w-3xl flex-col gap-10 px-6 py-14">
        <div className="flex justify-end">
          <SiteToolbar />
        </div>

        <header className="flex flex-col items-center text-center">
          <img
            src={logo}
            alt={t("home.logoAlt")}
            className="h-40 w-40 rounded-3xl object-cover"
            style={{ boxShadow: "var(--honey-glow)" }}
          />
          <h1 className="mt-6 text-4xl font-bold tracking-tight">
            Honey<span className="text-primary">Guard</span>
          </h1>
          <p className="mt-3 max-w-md text-sm text-muted-foreground">{t("home.tagline")}</p>
          <div className="mt-5 flex flex-wrap items-center justify-center gap-3">
            <Link
              to="/subir"
              className="rounded-xl px-5 py-2 text-sm font-semibold text-primary-foreground"
              style={{ backgroundImage: "var(--gradient-honey)" }}
            >
              Subir archivo →
            </Link>
            <Link
              to="/buscar"
              className="rounded-xl border border-border px-5 py-2 text-sm font-medium hover:border-primary"
            >
              Buscar contenidos
            </Link>
            <Link
              to="/biblioteca"
              className="rounded-xl border border-border px-5 py-2 text-sm font-medium hover:border-primary"
            >
              Biblioteca
            </Link>
          </div>
        </header>

        <section
          className="rounded-2xl border border-border p-6"
          style={{ backgroundColor: "var(--surface-elevated)" }}
        >
          <h2 className="text-lg font-semibold">Clasificar texto</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Pega un fragmento y el modelo devuelve categoría, probabilidad y palabras clave. Este
            paso no guarda nada: es solo inferencia.
          </p>

          <textarea
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            rows={6}
            placeholder="Pega aquí tu documentación, apunte o artículo…"
            className="mt-4 w-full resize-y rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-ring"
          />

          <button
            type="button"
            disabled={!texto.trim() || clasificacion.isPending}
            onClick={() => clasificacion.mutate()}
            className="mt-4 w-full rounded-xl px-6 py-2.5 text-sm font-semibold text-primary-foreground transition-opacity disabled:opacity-40"
            style={{ backgroundImage: "var(--gradient-honey)" }}
          >
            {clasificacion.isPending ? "Clasificando…" : "Clasificar"}
          </button>

          {clasificacion.isError && (
            <p className="mt-3 text-sm text-destructive">
              {(clasificacion.error as Error).message}
            </p>
          )}

          {resultado && (
            <div className="mt-6 flex flex-col gap-4 rounded-2xl border border-border bg-card p-5">
              <div>
                <p className="text-xs uppercase tracking-widest text-muted-foreground">Categoría</p>
                <p className="mt-1 text-lg font-semibold text-primary">{resultado.categoria}</p>
              </div>

              <div>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs uppercase tracking-widest text-muted-foreground">
                    {t("home.resultProbability")}
                  </p>
                  <span
                    className="text-sm font-semibold"
                    style={{ color: colorConfianza(resultado.probabilidad) }}
                  >
                    {porcentaje(resultado.probabilidad)}%
                  </span>
                </div>
                <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-secondary">
                  <div
                    className="h-full rounded-full"
                    style={{
                      width: `${porcentaje(resultado.probabilidad)}%`,
                      backgroundColor: colorConfianza(resultado.probabilidad),
                    }}
                  />
                </div>
              </div>

              <div>
                <p className="text-xs uppercase tracking-widest text-muted-foreground">
                  {t("home.resultKeywords")}
                </p>
                <ul className="mt-2 flex flex-wrap gap-2">
                  {resultado.palabras_clave.length === 0 && (
                    <li className="text-sm text-muted-foreground">Sin palabras clave</li>
                  )}
                  {resultado.palabras_clave.map((p) => (
                    <li
                      key={p}
                      className="rounded-full border border-border bg-secondary px-3 py-1 text-sm"
                    >
                      #{p}
                    </li>
                  ))}
                </ul>
              </div>

              {resultado.requiere_revision && (
                <p
                  className="rounded-xl border px-4 py-3 text-sm"
                  style={{
                    borderColor: "var(--confianza-media)",
                    color: "var(--confianza-media)",
                  }}
                >
                  ⚠️ La confianza es baja: conviene revisar la categoría manualmente.
                </p>
              )}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
