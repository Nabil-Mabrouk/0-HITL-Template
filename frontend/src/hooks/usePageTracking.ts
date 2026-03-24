import { useEffect } from "react";
import { useLocation } from "react-router-dom";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

/**
 * Hook à placer dans le composant racine.
 * Envoie un ping au backend à chaque changement de route React.
 * Fonctionne pour les utilisateurs connectés et anonymes.
 */
export function usePageTracking() {
  const location = useLocation();

  useEffect(() => {
    fetch(`${API}/api/track`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ path: location.pathname }),
      // Pas de credentials — les visites anonymes comptent aussi
    }).catch(() => {
      // Erreur silencieuse — le tracking ne doit jamais bloquer l'UX
    });
  }, [location.pathname]);
}