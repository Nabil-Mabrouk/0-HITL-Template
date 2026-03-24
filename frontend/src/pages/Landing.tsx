import { useTranslation } from "react-i18next";
import { WaitlistForm } from "../components/WaitlistForm";
import SEO from "../components/SEO";

export default function Landing() {
  const { t } = useTranslation("common");

  return (
    <>
      <SEO
        title="Zero Human In The Loop"
        description="L'automatisation intelligente arrive. Rejoignez la liste d'attente."
        url="/"
      />
      <main className="min-h-screen bg-black text-white flex flex-col
                       items-center justify-center px-4">
        {/* Badge */}
        <div className="mb-8 px-4 py-1.5 rounded-full border border-white/20
                        text-xs text-white/60 tracking-widest uppercase">
          {t("landing.construction")}
        </div>

        {/* Titre */}
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight
                       text-center mb-4">
          Zero Human
          <br />
          <span className="text-white/40">In The Loop</span>
        </h1>

        {/* Sous-titre */}
        <p className="text-white/50 text-lg text-center max-w-md mb-12 whitespace-pre-line">
          {t("landing.subtitle")}
        </p>

        {/* Formulaire waitlist */}
        <WaitlistForm />

        {/* Footer */}
        <p className="mt-16 text-white/20 text-sm">
          {t("landing.footer")}
        </p>
      </main>
    </>
  );
}
