import { createFileRoute, Link } from "@tanstack/react-router";

import logo from "@/assets/honeyguard-logo.png";

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
          </div>
        </header>

        <section
          className="rounded-2xl border border-border p-6"
          style={{ backgroundColor: "var(--surface-elevated)" }}
        >
          <h2 className="text-sm font-semibold text-foreground">Clasificar texto</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            La clasificación de texto suelto y la búsqueda de contenidos estarán disponibles
            cuando el backend exponga los endpoints <code className="text-foreground">/contenido</code> y{" "}
            <code className="text-foreground">/buscar</code>. Por ahora, el backend solo permite
            <strong> subir archivos</strong>.
          </p>
          <p className="mt-3 inline-flex items-center gap-2 rounded-full border border-border bg-secondary px-3 py-1 text-xs text-muted-foreground">
            <span className="h-2 w-2 rounded-full bg-muted-foreground" aria-hidden /> Próximamente
          </p>
        </section>
      </div>
    </main>
  );
}
