import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function RegisterDirect() {
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [success, setSuccess]   = useState(false);
  const navigate                = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    const res = await fetch(`${API}/api/auth/register-direct`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ email, password, full_name: fullName }),
    });

    if (res.ok) {
      setSuccess(true);
    } else {
      const err = await res.json();
      setError(err.detail ?? "Erreur lors de l'inscription");
    }
    setLoading(false);
  }

  if (success) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center
                      justify-center px-4 text-center">
        <div>
          <div className="text-4xl mb-4">✉️</div>
          <h1 className="text-2xl font-bold mb-4">Vérifiez votre email</h1>
          <p className="text-white/40 mb-8">
            Un lien de confirmation a été envoyé à <strong>{email}</strong>.
          </p>
          <button onClick={() => navigate("/login")}
                  className="text-white/60 hover:text-white transition underline">
            Aller à la connexion
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white flex items-center
                    justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-2 text-center">Créer un compte</h1>
        <p className="text-white/40 text-sm text-center mb-8">
          Accès direct — aucune invitation requise
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input type="text" placeholder="Nom complet (optionnel)"
                 value={fullName} onChange={e => setFullName(e.target.value)}
                 className="w-full bg-white/5 border border-white/10 rounded-lg
                            px-4 py-3 text-white placeholder-white/30 outline-none
                            focus:border-white/30 transition" />
          <input type="email" placeholder="Email" value={email}
                 onChange={e => setEmail(e.target.value)} required
                 className="w-full bg-white/5 border border-white/10 rounded-lg
                            px-4 py-3 text-white placeholder-white/30 outline-none
                            focus:border-white/30 transition" />
          <input type="password"
                 placeholder="Mot de passe (min. 8 car., 1 maj., 1 chiffre)"
                 value={password} onChange={e => setPassword(e.target.value)}
                 required
                 className="w-full bg-white/5 border border-white/10 rounded-lg
                            px-4 py-3 text-white placeholder-white/30 outline-none
                            focus:border-white/30 transition" />

          {error && <p className="text-red-400 text-sm text-center">{error}</p>}

          <button type="submit" disabled={loading}
                  className="w-full bg-white text-black font-semibold py-3
                             rounded-lg hover:bg-white/90 transition
                             disabled:opacity-50">
            {loading ? "Création..." : "Créer mon compte"}
          </button>
        </form>

        <div className="mt-6 text-center">
          <Link to="/login"
                className="text-white/40 hover:text-white/70 transition text-sm">
            Déjà un compte ? Se connecter
          </Link>
        </div>
      </div>
    </div>
  );
}