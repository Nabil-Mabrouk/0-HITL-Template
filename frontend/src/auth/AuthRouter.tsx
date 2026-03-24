/**
 * AuthRouter — point d'entrée unique pour l'authentification.
 *
 * Lit les variables d'environnement VITE_AUTH_CHANNEL_* et affiche
 * les options d'inscription disponibles.
 */

import { useNavigate } from "react-router-dom";

const CHANNEL_WAITLIST   = import.meta.env.VITE_AUTH_CHANNEL_WAITLIST   === "true";
const CHANNEL_DIRECT     = import.meta.env.VITE_AUTH_CHANNEL_DIRECT     === "true";
const CHANNEL_ONBOARDING = import.meta.env.VITE_AUTH_CHANNEL_ONBOARDING === "true";

export default function AuthRouter() {
  const navigate = useNavigate();

  // Un seul canal actif — redirection directe
  const activeCount = [CHANNEL_WAITLIST, CHANNEL_DIRECT,
                       CHANNEL_ONBOARDING].filter(Boolean).length;

  if (activeCount === 1) {
    if (CHANNEL_ONBOARDING) navigate("/join", { replace: true });
    if (CHANNEL_DIRECT)     navigate("/register-direct", { replace: true });
    if (CHANNEL_WAITLIST)   navigate("/", { replace: true });
    return null;
  }

  // Plusieurs canaux — afficher les options
  return (
    <div className="min-h-screen bg-black text-white flex items-center
                    justify-center px-4">
      <div className="w-full max-w-sm space-y-4">
        <h1 className="text-2xl font-bold text-center mb-8">
          Rejoindre la plateforme
        </h1>

        {CHANNEL_ONBOARDING && (
          <button
            onClick={() => navigate("/join")}
            className="w-full bg-white text-black font-semibold py-3
                       rounded-lg hover:bg-white/90 transition"
          >
            Découvrir mon profil →
          </button>
        )}

        {CHANNEL_DIRECT && (
          <button
            onClick={() => navigate("/register-direct")}
            className="w-full border border-white/20 text-white py-3
                       rounded-lg hover:bg-white/5 transition"
          >
            S'inscrire directement
          </button>
        )}

        {CHANNEL_WAITLIST && (
          <button
            onClick={() => navigate("/")}
            className="w-full border border-white/10 text-white/50 py-3
                       rounded-lg hover:bg-white/5 transition text-sm"
          >
            Rejoindre la liste d'attente
          </button>
        )}
      </div>
    </div>
  );
}