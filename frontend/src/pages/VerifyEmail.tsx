import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const token          = searchParams.get("token") ?? "";
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");

  useEffect(() => {
    if (!token) { setStatus("error"); return; }

    fetch(`${API}/api/auth/verify-email?token=${token}`)
      .then(res => setStatus(res.ok ? "success" : "error"))
      .catch(() => setStatus("error"));
  }, [token]);

  return (
    <div className="min-h-screen bg-black text-white flex items-center
                    justify-center text-center px-4">
      {status === "loading" && (
        <p className="text-white/40">Vérification en cours...</p>
      )}

      {status === "success" && (
        <div>
          <div className="text-4xl mb-4">✅</div>
          <h1 className="text-2xl font-bold mb-4">Email vérifié !</h1>
          <p className="text-white/40 mb-8">
            Ton compte est maintenant actif.
          </p>
          <Link
            to="/login"
            className="bg-white text-black font-semibold px-6 py-3
                       rounded-lg hover:bg-white/90 transition"
          >
            Se connecter
          </Link>
        </div>
      )}

      {status === "error" && (
        <div>
          <div className="text-4xl mb-4">❌</div>
          <h1 className="text-2xl font-bold mb-4">Lien invalide</h1>
          <p className="text-white/40 mb-8">
            Ce lien est invalide ou a expiré.
          </p>
          <Link to="/" className="text-white/60 hover:text-white transition underline">
            Retour à l'accueil
          </Link>
        </div>
      )}
    </div>
  );
}
