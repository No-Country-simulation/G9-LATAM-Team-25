import i18next from "i18next";
import { initReactI18next } from "react-i18next";

import es from "@/locales/es.json";
import en from "@/locales/en.json";

export const LANGUAGE_STORAGE_KEY = "honeyguard-lang";
export const DEFAULT_LANGUAGE = "es";
export const SUPPORTED_LANGUAGES = ["es", "en"] as const;
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number];

// El singleton de i18next se inicializa una sola vez con español como idioma
// por defecto. En el servidor este valor NUNCA cambia (evita fugas de estado
// entre solicitudes concurrentes); en el cliente, el idioma guardado se
// aplica después del montaje (ver I18nLanguageSync en __root.tsx) para que
// el primer render coincida siempre con el HTML generado por el servidor.
if (!i18next.isInitialized) {
  i18next.use(initReactI18next).init({
    resources: {
      es: { translation: es },
      en: { translation: en },
    },
    lng: DEFAULT_LANGUAGE,
    fallbackLng: DEFAULT_LANGUAGE,
    supportedLngs: SUPPORTED_LANGUAGES as unknown as string[],
    interpolation: { escapeValue: false },
    returnNull: false,
  });
}

export function readStoredLanguage(): SupportedLanguage {
  if (typeof window === "undefined") return DEFAULT_LANGUAGE;
  try {
    const stored = window.localStorage.getItem(LANGUAGE_STORAGE_KEY);
    return stored === "en" ? "en" : DEFAULT_LANGUAGE;
  } catch {
    return DEFAULT_LANGUAGE;
  }
}

export function persistLanguage(lang: SupportedLanguage) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, lang);
  } catch {
    // localStorage puede no estar disponible (modo privado); se ignora.
  }
}

export default i18next;
