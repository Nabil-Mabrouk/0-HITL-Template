import { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function ResetPassword() {
  const [searchParams]          = useSearchParams();
  const token                   = searchParams.get("token") ?? "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm]   = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [success, setSuccess]   = useState(false);
  const navigate                = useNavigate();

  if (!token) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center
                      justify-center text-center px-4">
        <p className="text-white/40">Lien invalide ou expiré.</p>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) { setError("Les mots de passe ne correspondent pas"); return; }
    setLoading(true);
    setError("");

    const res = await fetch(`${API}/api/auth/reset-password`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ token, password }),
    });

    if (res.ok) {
      setSuccess(true);
      setTimeout(() => navigate("/login"), 2000);
    } else {
      const err = await res.json();
      setError(err.detail ?? "Erreur lors de la réinitialisation");
    }
    setLoading(false);
  }

  if (success) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center
                      justify-center text-center px-4">
        <div>
          <div className="text-4xl mb-4">✅</div>
          <h1 className="text-2xl font-bold mb-2">Mot de passe modifié</h1>
          <p className="text-white/40">Redirection vers la connexion...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white flex items-center
                    justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-8 text-center">
          Nouveau mot de passe
        </h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="password"
            placeholder="Nouveau mot de passe"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            className="w-full bg-white/5 border border-white/10 rounded-lg
                       px-4 py-3 text-white placeholder-white/30 outline-none
                       focus:border-white/30 transition"
          />
          <input
            type="password"
            placeholder="Confirmer le mot de passe"
            value={confirm}
            onChange={e => setConfirm(e.target.value)}
            required
            className="w-full bg-white/5 border border-white/10 rounded-lg
                       px-4 py-3 text-white placeholder-white/30 outline-none
                       focus:border-white/30 transition"
          />

          {error && <p className="text-red-400 text-sm text-center">{error}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-white text-black font-semibold py-3 rounded-lg
                       hover:bg-white/90 transition disabled:opacity-50"
          >
            {loading ? "Modification..." : "Modifier le mot de passe"}
          </button>
        </form>
      </div>
    </div>
  );
}
