import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";
import i18n, { readStoredLanguage } from "../i18n/config";
import { THEME_STORAGE_KEY, ThemeProvider } from "../contexts/theme-context";

// Script inline sin parpadeo: se ejecuta de forma síncrona antes de que el
// navegador pinte la página, así que aplica la clase "dark" (si corresponde)
// antes de la hidratación de React. Al no depender de React, no genera
// advertencias de hidratación por SSR.
const THEME_INIT_SCRIPT = `(function(){try{var s=localStorage.getItem(${JSON.stringify(
  THEME_STORAGE_KEY,
)});var t=s==='light'||s==='dark'?s:'system';var d=t==='dark'||(t==='system'&&window.matchMedia('(prefers-color-scheme: dark)').matches);if(d)document.documentElement.classList.add('dark');}catch(e){}})();`;

function NotFoundComponent() {
  const { t } = useTranslation();
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">{t("notFound.title")}</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">{t("notFound.heading")}</h2>
        <p className="mt-2 text-sm text-muted-foreground">{t("notFound.description")}</p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            {t("notFound.goHome")}
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  const { t } = useTranslation();
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          {t("errorPage.heading")}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">{t("errorPage.description")}</p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => {
              router.invalidate();
              reset();
            }}
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            {t("errorPage.retry")}
          </button>
          <a
            href="/"
            className="inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            {t("errorPage.goHome")}
          </a>
        </div>
      </div>
    </div>
  );
}

// Sincroniza el idioma guardado en localStorage después del montaje. El
// primer render del cliente siempre coincide con el español del servidor
// (evita errores de hidratación); este efecto solo se dispara una vez.
function I18nLanguageSync() {
  useEffect(() => {
    const stored = readStoredLanguage();
    if (stored !== i18n.language) {
      void i18n.changeLanguage(stored);
    }
    document.documentElement.lang = stored;
  }, []);
  return null;
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "HoneyGuard — Clasifica y organiza tu contenido técnico" },
      {
        name: "description",
        content:
          "HoneyGuard clasifica documentación, artículos, apuntes y tutoriales para que reutilices tu conocimiento técnico en segundos.",
      },
      { name: "author", content: "Lovable" },
      { property: "og:title", content: "HoneyGuard — Clasifica y organiza tu contenido técnico" },
      {
        property: "og:description",
        content:
          "HoneyGuard clasifica documentación, artículos, apuntes y tutoriales para que reutilices tu conocimiento técnico en segundos.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:site", content: "@Lovable" },
      { name: "twitter:title", content: "HoneyGuard — Clasifica y organiza tu contenido técnico" },
      {
        name: "twitter:description",
        content:
          "HoneyGuard clasifica documentación, artículos, apuntes y tutoriales para que reutilices tu conocimiento técnico en segundos.",
      },
      {
        property: "og:image",
        content:
          "https://storage.googleapis.com/gpt-engineer-file-uploads/7D8vUXRP30MIH87cWp8srlhOKeN2/social-images/social-1785184358504-ChatGPT_Image_27_jul_2026,_14_05_49.webp",
      },
      {
        name: "twitter:image",
        content:
          "https://storage.googleapis.com/gpt-engineer-file-uploads/7D8vUXRP30MIH87cWp8srlhOKeN2/social-images/social-1785184358504-ChatGPT_Image_27_jul_2026,_14_05_49.webp",
      },
    ],
    links: [
      {
        rel: "stylesheet",
        href: appCss,
      },
      { rel: "icon", type: "image/png", href: "/favicon.png" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang={i18n.language} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <I18nLanguageSync />
        {/* Required: nested routes render here. Removing <Outlet /> breaks all child routes. */}
        <Outlet />
      </ThemeProvider>
    </QueryClientProvider>
  );
}
