import { useTranslation } from "react-i18next";

import { persistLanguage, type SupportedLanguage } from "@/i18n/config";

export function LanguageToggle() {
  const { t, i18n } = useTranslation();
  const current: SupportedLanguage = i18n.language?.startsWith("en") ? "en" : "es";

  function changeLanguage(lang: SupportedLanguage) {
    if (lang === current) return;
    void i18n.changeLanguage(lang);
    document.documentElement.lang = lang;
    persistLanguage(lang);
  }

  return (
    <div
      role="group"
      aria-label={t("language.selectorLabel")}
      className="inline-flex items-center rounded-xl border border-border p-0.5"
    >
      <button
        type="button"
        onClick={() => changeLanguage("es")}
        aria-pressed={current === "es"}
        className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition-colors ${
          current === "es"
            ? "bg-secondary text-secondary-foreground"
            : "text-muted-foreground hover:text-foreground"
        }`}
      >
        ES
      </button>
      <button
        type="button"
        onClick={() => changeLanguage("en")}
        aria-pressed={current === "en"}
        className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition-colors ${
          current === "en"
            ? "bg-secondary text-secondary-foreground"
            : "text-muted-foreground hover:text-foreground"
        }`}
      >
        EN
      </button>
    </div>
  );
}
