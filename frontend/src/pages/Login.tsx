import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTranslation } from "react-i18next";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export default function Login() {
  const { t } = useTranslation("auth");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const { login }               = useAuth();
  const navigate                = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    const res = await fetch(`${API}/api/auth/login`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ email, password }),
      credentials: "include", // Permet de recevoir le cookie refresh_token
    });

    if (res.ok) {
      const data = await res.json();
      await login(data.access_token);
      navigate("/profile");
    } else {
      const err = await res.json();
      setError(err.detail ?? t("login.error"));
    }
    setLoading(false);
  }

  return (
    <div className="min-h-screen bg-black text-white flex items-center
                    justify-center px-4">
      <div className="w-full max-w-sm">
        <h1 className="text-2xl font-bold mb-8 text-center">{t("login.title")}</h1>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email"
            placeholder={t("login.email")}
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            className="w-full bg-white/5 border border-white/10 rounded-lg
                       px-4 py-3 text-white placeholder-white/30 outline-none
                       focus:border-white/30 transition"
          />
          <input
            type="password"
            placeholder={t("login.password")}
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
            {loading ? t("login.loading") : t("login.submit")}
          </button>
        </form>

        <div className="mt-6 flex flex-col gap-2 text-center text-sm text-white/40">
          <Link to="/forgot-password" university-none className="hover:text-white/70 transition">
            {t("login.forgot")}
          </Link>
          <Link to="/" className="hover:text-white/70 transition">
            {t("login.back")}
          </Link>
        </div>
      </div>
    </div>
  );
}
