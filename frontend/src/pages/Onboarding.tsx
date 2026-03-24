import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface Step {
  id:       string;
  type:     string;
  question: string;
  options:  { value: string; label: string }[];
}

interface FlowConfig {
  id:          string;
  title:       string;
  description: string;
  steps:       Step[];
}

interface ResultScreen {
  title:         string;
  description:   string;
  show_score:    boolean;
  score:         number;
  label:         string;
  cta_primary:   string;
  cta_secondary: string | null;
}

type Phase = "loading" | "questions" | "result" | "register" | "success";

export default function Onboarding() {
  const navigate                    = useNavigate();
  const [searchParams]              = useSearchParams();
  const { user, accessToken }       = useAuth();
  const isUpdate                    = (searchParams.get("update") === "true") || (user !== null);

  const [flow, setFlow]             = useState<FlowConfig | null>(null);
  const [phase, setPhase]           = useState<Phase>("loading");
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers]       = useState<Record<string, string>>({});
  const [resultScreen, setResultScreen] = useState<ResultScreen | null>(null);
  const [scoringResult, setScoringResult] = useState<Record<string, string>>({});

  // Formulaire d'inscription (mode non connecté uniquement)
  const [email, setEmail]           = useState("");
  const [password, setPassword]     = useState("");
  const [fullName, setFullName]     = useState("");
  const [error, setError]           = useState("");
  const [loading, setLoading]       = useState(false);

  useEffect(() => {
    fetch(`${API}/api/onboarding/flow`)
      .then(r => r.json())
      .then(data => { setFlow(data); setPhase("questions"); })
      .catch(() => navigate("/"));
  }, []);

  async function handleAnswer(stepId: string, value: string) {
    const newAnswers = { ...answers, [stepId]: value };
    setAnswers(newAnswers);
    if (!flow) return;

    if (currentStep < flow.steps.length - 1) {
      setCurrentStep(s => s + 1);
    } else {
      // Dernière question — évaluer
      try {
        const res = await fetch(`${API}/api/onboarding/evaluate`, {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify({ answers: newAnswers }),
        });
        if (res.ok) {
          const data = await res.json();
          setResultScreen(data.screen);
          setScoringResult(data.result);
          setPhase("result");
        } else {
          setError("Erreur lors de l'évaluation du profil. Réessayez.");
        }
      } catch (err) {
        setError("Impossible de contacter le serveur.");
      }
    }
  }

  // Mode update — user connecté qui refait l'onboarding
  async function handleUpdateProfile() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/onboarding/update-profile`, {
        method:  "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization:  `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ answers }),
      });
      if (res.ok) {
        navigate("/profile?updated=true");
      } else {
        const err = await res.json();
        setError(err.detail ?? "Erreur lors de la mise à jour");
      }
    } catch (err) {
      setError("Erreur réseau lors de la mise à jour.");
    }
    setLoading(false);
  }

  // Mode register — nouvel utilisateur
  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/api/onboarding/register`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ email, password, full_name: fullName, answers }),
      });
      if (res.ok) {
        setPhase("success");
      } else {
        const err = await res.json();
        setError(err.detail ?? "Erreur lors de l'inscription");
      }
    } catch (err) {
      setError("Erreur réseau lors de l'inscription.");
    }
    setLoading(false);
  }

  // ── Loading ────────────────────────────────────────────────────────────────
  if (phase === "loading" || !flow) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center
                      justify-center">
        <p className="text-white/40">Chargement...</p>
      </div>
    );
  }

  // ── Questions ──────────────────────────────────────────────────────────────
  if (phase === "questions") {
    const step     = flow.steps[currentStep];
    const progress = (currentStep / flow.steps.length) * 100;

    return (
      <div className="min-h-screen bg-black text-white flex items-center
                      justify-center px-4">
        <div className="w-full max-w-lg">

          {/* Header */}
          <div className="mb-10">
            <div className="flex items-center justify-between mb-2">
              <p className="text-white/40 text-sm">{flow.title}</p>
              {isUpdate && (
                <button onClick={() => navigate("/profile")}
                        className="text-white/30 hover:text-white/60 transition
                                   text-xs">
                  Annuler
                </button>
              )}
            </div>
            <div className="w-full bg-white/10 rounded-full h-1">
              <div className="bg-white rounded-full h-1 transition-all duration-500"
                   style={{ width: `${progress}%` }} />
            </div>
            <p className="text-white/30 text-xs mt-2 text-right">
              {currentStep + 1} / {flow.steps.length}
            </p>
          </div>

          {/* Question */}
          <h2 className="text-2xl font-bold mb-8">{step.question}</h2>

          {/* Options */}
          <div className="space-y-3">
            {step.options.map(opt => (
              <button
                key={opt.value}
                onClick={() => handleAnswer(step.id, opt.value)}
                className="w-full text-left px-6 py-4 border border-white/10
                           rounded-xl hover:border-white/40 hover:bg-white/5
                           transition"
              >
                {opt.label}
              </button>
            ))}
          </div>

          {/* Retour */}
          {currentStep > 0 && (
            <button
              onClick={() => setCurrentStep(s => s - 1)}
              className="mt-6 text-white/30 hover:text-white/60 transition text-sm"
            >
              ← Question précédente
            </button>
          )}
        </div>
      </div>
    );
  }

  // ── Résultat ───────────────────────────────────────────────────────────────
  if (phase === "result" && resultScreen) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center
                      justify-center px-4">
        <div className="w-full max-w-md text-center">

          {resultScreen.show_score && (
            <div className="w-24 h-24 rounded-full border-4 border-white/20
                            flex items-center justify-center mx-auto mb-8">
              <span className="text-3xl font-bold">{resultScreen.score}</span>
            </div>
          )}

          <h1 className="text-3xl font-bold mb-4">{resultScreen.title}</h1>
          <p className="text-white/50 mb-10">{resultScreen.description}</p>

          {error && <p className="text-red-400 text-sm mb-4">{error}</p>}

          <div className="space-y-3">
            {isUpdate ? (
              // Mode update — user connecté
              <>
                <button
                  onClick={handleUpdateProfile}
                  disabled={loading}
                  className="w-full bg-white text-black font-semibold py-3
                             rounded-lg hover:bg-white/90 transition
                             disabled:opacity-50"
                >
                  {loading ? "Mise à jour..." : "Mettre à jour mon profil"}
                </button>
                <button
                  onClick={() => navigate("/profile")}
                  className="w-full border border-white/10 text-white/40 py-3
                             rounded-lg hover:bg-white/5 transition text-sm"
                >
                  Annuler
                </button>
              </>
            ) : (
              // Mode register — nouvel utilisateur
              <>
                <button
                  onClick={() => setPhase("register")}
                  className="w-full bg-white text-black font-semibold py-3
                             rounded-lg hover:bg-white/90 transition"
                >
                  {resultScreen.cta_primary}
                </button>
                {resultScreen.cta_secondary && (
                  <button className="w-full border border-white/20 text-white/60
                                     py-3 rounded-lg hover:bg-white/5 transition">
                    {resultScreen.cta_secondary}
                  </button>
                )}
              </>
            )}
          </div>

          <button
            onClick={() => { setCurrentStep(flow.steps.length - 1); setPhase("questions"); }}
            className="mt-6 text-white/30 hover:text-white/60 transition text-sm"
          >
            ← Modifier mes réponses
          </button>
        </div>
      </div>
    );
  }

  // ── Inscription ────────────────────────────────────────────────────────────
  if (phase === "register") {
    return (
      <div className="min-h-screen bg-black text-white flex items-center
                      justify-center px-4">
        <div className="w-full max-w-sm">
          <h1 className="text-2xl font-bold mb-2 text-center">
            Créer votre compte
          </h1>
          <p className="text-white/40 text-sm text-center mb-8">
            Profil : <strong className="text-white/70">{scoringResult.label}</strong>
          </p>

          <form onSubmit={handleRegister} className="space-y-4">
            <input
              type="text"
              placeholder="Nom complet (optionnel)"
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              className="w-full bg-white/5 border border-white/10 rounded-lg
                         px-4 py-3 text-white placeholder-white/30 outline-none
                         focus:border-white/30 transition"
            />
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
            <input
              type="password"
              placeholder="Mot de passe (min. 8 car., 1 maj., 1 chiffre)"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              className="w-full bg-white/5 border border-white/10 rounded-lg
                         px-4 py-3 text-white placeholder-white/30 outline-none
                         focus:border-white/30 transition"
            />

            {error && <p className="text-red-400 text-sm text-center">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-white text-black font-semibold py-3
                         rounded-lg hover:bg-white/90 transition disabled:opacity-50"
            >
              {loading ? "Création..." : "Créer mon compte"}
            </button>
          </form>

          <button
            onClick={() => setPhase("result")}
            className="mt-4 w-full text-white/30 hover:text-white/60
                       transition text-sm text-center"
          >
            ← Voir mon profil
          </button>
        </div>
      </div>
    );
  }

  // ── Succès ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-black text-white flex items-center
                    justify-center px-4 text-center">
      <div>
        <div className="text-4xl mb-4">✉️</div>
        <h1 className="text-2xl font-bold mb-4">Vérifiez votre email</h1>
        <p className="text-white/40 mb-8">
          Un lien de confirmation a été envoyé à <strong>{email}</strong>.
        </p>
        <button
          onClick={() => navigate("/login")}
          className="text-white/60 hover:text-white transition underline"
        >
          Aller à la connexion
        </button>
      </div>
    </div>
  );
}
