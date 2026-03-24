import { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function Register() {
  const { t } = useTranslation("auth");
  const [searchParams]          = useSearchParams();
  const invitationToken         = searchParams.get("invitation") ?? "";

  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [success, setSuccess]   = useState(false);
  const navigate                = useNavigate();

  if (!invitationToken) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center
                      justify-center px-4 text-center">
        <div>
          <h1 className="text-2xl font-bold mb-4">{t("register.access_denied")}</h1>
          <p className="text-white/40 mb-8 whitespace-pre-line">
            {t("register.no_invitation")}
          </p>
          <Link to="/" className="text-white/60 hover:text-white transition underline">
            {t("register.join_waitlist")}
          </Link>
        </div>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    const res = await fetch(`${API}/api/auth/register`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({
        email,
        password,
        full_name:        fullName,
        invitation_token: invitationToken,
      }),
    });

    if (res.ok) {
      setSuccess(true);
    } else {
      const err = await res.json();
      setError(err.detail ?? t("register.error")); // On pourrait ajouter une clé plus spécifique
    }
    setLoading(false);
  }

  if (success) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center
                      justify-center px-4 text-center">
        <div>
          <div className="text-4xl mb-4">✉️</div>
          <h1 className="text-2xl font-bold mb-4">{t("register.success_title")}</h1>
          <p className="text-white/40 mb-8">
            {t("register.success_body", { email })}
          </p>
          <button
            onClick={() => navigate("/login")}
            className="text-white/60 hover:text-white transition underline"
          >
            {t("register.back_login")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white flex items-center
                    justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-2 text-center">{t("register.title")}</h1>
        <p className="text-white/40 text-sm text-center mb-8">
          {t("register.subtitle")}
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder={t("register.full_name")}
            value={fullName}
            onChange={e => setFullName(e.target.value)}
            className="w-full bg-white/5 border border-white/10 rounded-lg
                       px-4 py-3 text-white placeholder-white/30 outline-none
                       focus:border-white/30 transition"
          />
          <input
            type="email"
            placeholder={t("register.email")}
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            className="w-full bg-white/5 border border-white/10 rounded-lg
                       px-4 py-3 text-white placeholder-white/30 outline-none
                       focus:border-white/30 transition"
          />
          <input
            type="password"
            placeholder={t("register.password_hint")}
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            className="w-full bg-white/5 border border-white/10 rounded-lg
                       px-4 py-3 text-white placeholder-white/30 outline-none
                       focus:border-white/30 transition"
          />

          {error && (
            <p className="text-red-400 text-sm text-center">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-white text-black font-semibold py-3 rounded-lg
                       hover:bg-white/90 transition disabled:opacity-50"
          >
            {loading ? t("register.loading") : t("register.submit")}
          </button>
        </form>
      </div>
    </div>
  );
}
