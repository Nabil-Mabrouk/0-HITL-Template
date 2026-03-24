import { useState } from "react";
import { Link } from "react-router-dom";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function ForgotPassword() {
  const [email, setEmail]     = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent]       = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    await fetch(`${API}/api/auth/forgot-password`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ email }),
    });
    setSent(true);
    setLoading(false);
  }

  if (sent) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center
                      justify-center px-4 text-center">
        <div>
          <div className="text-4xl mb-4">✉️</div>
          <h1 className="text-2xl font-bold mb-4">Email envoyé</h1>
          <p className="text-white/40 mb-8">
            Si cet email existe, un lien de réinitialisation a été envoyé.
          </p>
          <Link to="/login" className="text-white/60 hover:text-white transition underline">
            Retour à la connexion
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white flex items-center
                    justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-2 text-center">Mot de passe oublié</h1>
        <p className="text-white/40 text-sm text-center mb-8">
          Saisis ton email pour recevoir un lien de réinitialisation.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            className="w-full bg-white/5 border border-white/10 rounded-lg
                       px-4 py-3 text-white placeholder-white/30 outline-none
                       focus:border-white/30 transition"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-white text-black font-semibold py-3 rounded-lg
                       hover:bg-white/90 transition disabled:opacity-50"
          >
            {loading ? "Envoi..." : "Envoyer le lien"}
          </button>
        </form>

        <div className="mt-6 text-center">
          <Link to="/login" className="text-white/40 hover:text-white/70 transition text-sm">
            ← Retour à la connexion
          </Link>
        </div>
      </div>
    </div>
  );
}
