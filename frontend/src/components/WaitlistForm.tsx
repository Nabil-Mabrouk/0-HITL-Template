import { useState } from "react";
import { useTranslation } from "react-i18next";

type Status = "idle" | "loading" | "success" | "error";

export function WaitlistForm() {
  const { t } = useTranslation("common");
  const [email, setEmail]   = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [message, setMessage] = useState("");

  const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;

    setStatus("loading");

    try {
      const res = await fetch(`${API_URL}/api/waitlist`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ email }),
      });

      if (!res.ok) throw new Error("Server error");

      const data = await res.json();
      // On utilise le message du backend s'il existe, sinon notre clé de trad
      setMessage(data.message || t("waitlist.success"));
      setStatus("success");
      setEmail("");
    } catch {
      setStatus("error");
      setMessage(t("waitlist.error"));
    }
  }

  if (status === "success") {
    return (
      <div className="text-center">
        <div className="text-4xl mb-4">✓</div>
        <p className="text-white/80">{message}</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit}
          className="flex flex-col sm:flex-row gap-3 w-full max-w-md">

      <input
        type="email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        placeholder={t("waitlist.placeholder")}
        required
        disabled={status === "loading"}
        className="flex-1 px-4 py-3 rounded-lg bg-white/10 border
                   border-white/20 text-white placeholder:text-white/30
                   focus:outline-none focus:border-white/50
                   disabled:opacity-50 transition"
      />

      <button
        type="submit"
        disabled={status === "loading"}
        className="px-6 py-3 rounded-lg bg-white text-black font-medium
                   hover:bg-white/90 disabled:opacity-50
                   transition whitespace-nowrap"
      >
        {status === "loading" ? "..." : t("waitlist.button")}
      </button>

      {status === "error" && (
        <p className="w-full text-red-400 text-sm mt-1">{message}</p>
      )}
    </form>
  );
}
