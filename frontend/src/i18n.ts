import i18n               from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector   from "i18next-browser-languagedetector";
import HttpBackend        from "i18next-http-backend";

i18n
  .use(HttpBackend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    fallbackLng:   "fr",
    supportedLngs: ["fr", "en"],
    defaultNS:     "common",
    ns:            ["common", "auth", "learn", "admin", "profile"],

    backend: {
      loadPath: "/locales/{{lng}}/{{ns}}.json",
    },

    detection: {
      order:               ["localStorage", "navigator"],
      caches:              ["localStorage"],
      lookupLocalStorage:  "i18n_lang",
    },

    interpolation: {
      escapeValue: false,
    },
  });

// Synchroniser la direction du texte (RTL pour l'arabe)
i18n.on("languageChanged", (lng) => {
  document.documentElement.lang = lng;
  document.documentElement.dir  = lng === "ar" ? "rtl" : "ltr";
});

export default i18n;
