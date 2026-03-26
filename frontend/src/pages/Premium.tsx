import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useSearchParams } from "react-router-dom";
import SEO from "../components/SEO";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface Plan {
  id:             string;
  product_name:   string;
  unit_amount:    number;
  currency:       string;
  interval:       string;
  interval_count: number;
}

interface SubStatus {
  status:             string;
  is_premium:         boolean;
  current_period_end: string | null;
  trial_end:          string | null;
  cancelled_at:       string | null;
}

function formatInterval(interval: string, count: number) {
  if (interval === "month" && count === 1) return "/ mois";
  if (interval === "year"  && count === 1) return "/ an";
  return `/ ${count} ${interval}`;
}

function formatPrice(cents: number, currency: string) {
  return new Intl.NumberFormat("fr-FR", {
    style:    "currency",
    currency: currency.toUpperCase(),
  }).format(cents / 100);
}

export default function Premium() {
  const { user, accessToken } = useAuth();
  const [searchParams]        = useSearchParams();

  const [plans,    setPlans]    = useState<Plan[]>([]);
  const [subStatus, setSubStatus] = useState<SubStatus | null>(null);
  const [loading,  setLoading]  = useState(true);
  const [buying,   setBuying]   = useState<string | null>(null);
  const [portalLoading, setPortalLoading] = useState(false);

  const justSubscribed = searchParams.get("subscribed") === "1";

  const headers = {
    "Content-Type": "application/json",
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
  };

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/subscription/plans`).then(r => r.ok ? r.json() : []),
      user
        ? fetch(`${API}/api/subscription/status`, { headers }).then(r => r.ok ? r.json() : null)
        : Promise.resolve(null),
    ]).then(([p, s]) => {
      setPlans(p);
      setSubStatus(s);
    }).finally(() => setLoading(false));
  }, [user]);

  async function handleSubscribe(priceId: string) {
    if (!user) {
      window.location.href = "/login?next=/premium";
      return;
    }
    setBuying(priceId);
    try {
      const res = await fetch(`${API}/api/subscription/checkout`, {
        method: "POST",
        headers,
        body: JSON.stringify({ price_id: priceId }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? "Erreur");
      }
      const { checkout_url } = await res.json();
      window.location.href = checkout_url;
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : "Erreur lors du paiement");
      setBuying(null);
    }
  }

  async function handlePortal() {
    setPortalLoading(true);
    try {
      const res = await fetch(`${API}/api/subscription/portal`, {
        method: "POST",
        headers,
        body: JSON.stringify({ return_url: window.location.href }),
      });
      const { portal_url } = await res.json();
      window.location.href = portal_url;
    } catch {
      alert("Impossible d'ouvrir le portail de gestion.");
      setPortalLoading(false);
    }
  }

  const isPremium = subStatus?.is_premium || user?.role === "premium" || user?.role === "admin";

  return (
    <>
      <SEO
        title="Premium"
        description="Accédez à tout le contenu premium avec un abonnement mensuel."
        url="/premium"
      />
      <main className="min-h-screen bg-black text-white px-4 py-16">
        <div className="max-w-3xl mx-auto">

          {/* ── Header ─────────────────────────────────────────── */}
          <div className="text-center mb-12">
            <div className="inline-block px-3 py-1 rounded-full border border-yellow-500/40
                            text-yellow-400 text-xs tracking-widest uppercase mb-4">
              Premium
            </div>
            <h1 className="text-4xl font-bold mb-3">Accès illimité</h1>
            <p className="text-white/60 max-w-md mx-auto">
              Débloquez tous les tutoriels, ressources et fonctionnalités avancées.
            </p>
          </div>

          {justSubscribed && (
            <div className="mb-8 p-4 rounded-xl border border-green-500/30
                            bg-green-500/10 text-green-400 text-center">
              🎉 Abonnement activé ! Bienvenue dans Premium.
            </div>
          )}

          {/* ── Already premium ────────────────────────────────── */}
          {isPremium && !justSubscribed && (
            <div className="mb-8 p-6 rounded-xl border border-yellow-500/30
                            bg-yellow-500/5 text-center">
              <p className="text-yellow-400 font-semibold text-lg mb-2">
                ✨ Vous êtes déjà Premium
              </p>
              {subStatus?.current_period_end && (
                <p className="text-white/50 text-sm">
                  Renouvellement le{" "}
                  {new Date(subStatus.current_period_end).toLocaleDateString("fr-FR")}
                </p>
              )}
              {subStatus?.cancelled_at && (
                <p className="text-orange-400 text-sm mt-1">
                  Abonnement annulé — accès jusqu'à la fin de la période.
                </p>
              )}
              <button
                onClick={handlePortal}
                disabled={portalLoading}
                className="mt-4 px-5 py-2 border border-white/20 rounded-lg text-sm
                           hover:border-white/40 transition disabled:opacity-50"
              >
                {portalLoading ? "Redirection…" : "Gérer mon abonnement"}
              </button>
            </div>
          )}

          {/* ── Plans ──────────────────────────────────────────── */}
          {loading && <p className="text-white/40 text-center">Chargement…</p>}

          {!loading && plans.length === 0 && (
            <p className="text-white/40 text-center">
              Aucun plan disponible pour l'instant.
            </p>
          )}

          <div className="grid gap-6 sm:grid-cols-2">
            {plans.map(plan => (
              <div
                key={plan.id}
                className="border border-white/10 rounded-xl p-6
                           hover:border-white/30 transition-colors"
              >
                <p className="text-white/50 text-xs uppercase tracking-widest mb-1">
                  {plan.product_name}
                </p>
                <div className="flex items-end gap-1 mb-4">
                  <span className="text-3xl font-bold">
                    {formatPrice(plan.unit_amount, plan.currency)}
                  </span>
                  <span className="text-white/40 text-sm mb-1">
                    {formatInterval(plan.interval, plan.interval_count)}
                  </span>
                </div>
                <button
                  onClick={() => handleSubscribe(plan.id)}
                  disabled={!!buying || isPremium}
                  className="w-full py-2.5 bg-white text-black rounded-lg font-medium
                             text-sm hover:bg-white/90 disabled:opacity-40
                             disabled:cursor-not-allowed transition"
                >
                  {buying === plan.id
                    ? "Redirection…"
                    : isPremium
                    ? "Déjà abonné"
                    : user
                    ? "S'abonner"
                    : "Se connecter pour s'abonner"}
                </button>
              </div>
            ))}
          </div>

          {/* ── Features list ──────────────────────────────────── */}
          <div className="mt-16 border-t border-white/10 pt-10">
            <h2 className="text-xl font-semibold mb-6 text-center">Ce que vous obtenez</h2>
            <ul className="space-y-3 max-w-md mx-auto text-white/70">
              {[
                "Accès à tous les tutoriels Premium",
                "Contenu mis à jour chaque semaine",
                "Annulation à tout moment",
              ].map(item => (
                <li key={item} className="flex gap-3 items-start">
                  <span className="text-yellow-400 mt-0.5">✓</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>

        </div>
      </main>
    </>
  );
}
