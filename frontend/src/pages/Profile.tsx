import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTranslation } from "react-i18next";
import SEO from "../components/SEO";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface OnboardingProfile {
  flow_id:    string;
  profile:    string;
  score:      number | null;
  answers:    Record<string, string>;
  updated_at: string;
}

export default function Profile() {
  const { user, accessToken, logout } = useAuth();
  const navigate                      = useNavigate();
  const [searchParams]                = useSearchParams();
  const { t, i18n }                   = useTranslation("profile");

  const [fullName, setFullName]           = useState(user?.full_name ?? "");
  const [currentPwd, setCurrentPwd]       = useState("");
  const [newPwd, setNewPwd]               = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState("");

  const [flashMsg, setFlashMsg]       = useState("");
  const [pwdMsg, setPwdMsg]           = useState("");
  const [pwdError, setPwdError]       = useState("");
  const [deleteError, setDeleteError] = useState("");
  const [showDelete, setShowDelete]   = useState(false);

  const [onboardingProfile, setOnboardingProfile] = useState<OnboardingProfile | null>(null);
  const [onboardingLoading, setOnboardingLoading] = useState(false);

  const headers = {
    "Content-Type": "application/json",
    Authorization:  `Bearer ${accessToken}`,
  };

  useEffect(() => {
    setOnboardingLoading(true);
    fetch(`${API}/api/onboarding/my-profile`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => setOnboardingProfile(data))
      .catch(() => setOnboardingProfile(null))
      .finally(() => setOnboardingLoading(false));
  }, []);

  useEffect(() => {
    if (searchParams.get("updated") === "true") {
      setFlashMsg(t("info.updated_usage"));
      setTimeout(() => setFlashMsg(""), 4000);
    }
  }, [searchParams, t]);

  async function updateProfile(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch(`${API}/api/users/me`, {
      method: "PUT", headers,
      body: JSON.stringify({ full_name: fullName }),
    });
    setFlashMsg(res.ok ? t("info.success") : t("info.error"));
    setTimeout(() => setFlashMsg(""), 3000);
  }

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    setPwdError("");
    const res = await fetch(`${API}/api/users/me/password`, {
      method: "PUT", headers,
      body: JSON.stringify({ current_password: currentPwd, new_password: newPwd }),
    });
    if (res.ok) {
      setPwdMsg(t("password.success"));
      setTimeout(() => { logout(); navigate("/login"); }, 2000);
    } else {
      const err = await res.json();
      setPwdError(err.detail ?? t("password.error"));
    }
  }

  async function deleteAccount() {
    const res = await fetch(`${API}/api/users/me`, {
      method: "DELETE", headers,
      body: JSON.stringify({ password: deleteConfirm }),
    });
    if (res.ok) { logout(); navigate("/"); }
    else {
      const err = await res.json();
      setDeleteError(err.detail ?? t("password.error"));
    }
  }

  const profileEmojis: Record<string, string> = {
    power_user: "🚀", enterprise: "🏢", builder: "🔧", explorer: "🧭", standard: "👤",
  };

  return (
    <>
      <SEO title={user?.full_name || t("title")} noindex={true} />
      <div className="min-h-screen bg-black text-white">
        <div className="max-w-lg mx-auto px-6 py-12 space-y-10">

          {/* Message flash */}
          {flashMsg && (
            <div className="px-4 py-3 bg-green-500/10 border border-green-500/20
                            text-green-400 rounded-lg text-sm">
              {flashMsg}
            </div>
          )}

          {/* Infos utilisateur */}
          <div>
            <h1 className="text-2xl font-bold mb-1">
              {user?.full_name || t("title")}
            </h1>
            <p className="text-white/40 text-sm">{user?.email}</p>
          </div>

          {/* ── Onboarding ─────────────────────────────────────────────── */}
          <section className="border border-white/10 rounded-xl p-6">
            <h2 className="text-lg font-semibold mb-4">{t("usage_profile.title")}</h2>

            {onboardingLoading ? (
              <p className="text-white/30 text-sm">{t("usage_profile.loading")}</p>
            ) : onboardingProfile ? (
              <div className="space-y-4">
                {(() => {
                  const emoji = profileEmojis[onboardingProfile.profile] ?? "👤";
                  // Récupérer labels traduits
                  const label = t(`usage_profile.labels.${onboardingProfile.profile}.label`, { defaultValue: onboardingProfile.profile });
                  const desc  = t(`usage_profile.labels.${onboardingProfile.profile}.desc`, { defaultValue: "" });

                  return (
                    <div className="flex items-start gap-4">
                      <span className="text-3xl">{emoji}</span>
                      <div className="flex-1">
                        <p className="font-semibold">{label}</p>
                        <p className="text-white/40 text-sm">{desc}</p>
                      </div>
                      {onboardingProfile.score !== null && (
                        <div className="text-right">
                          <p className="text-2xl font-bold">{onboardingProfile.score}</p>
                          <p className="text-white/30 text-xs">{t("usage_profile.score")}</p>
                        </div>
                      )}
                    </div>
                  );
                })()}

                {Object.keys(onboardingProfile.answers).length > 0 && (
                  <div className="border-t border-white/10 pt-4 space-y-2">
                    <p className="text-white/30 text-xs uppercase tracking-wider mb-3">
                      {t("usage_profile.answers_title")}
                    </p>
                    {Object.entries(onboardingProfile.answers).map(([key, val]) => (
                      <div key={key} className="flex justify-between text-sm">
                        <span className="text-white/40 capitalize">
                          {key.replace(/_/g, " ")}
                        </span>
                        <span className="text-white/70">{val}</span>
                      </div>
                    ))}
                  </div>
                )}

                <p className="text-white/20 text-xs">
                  {t("usage_profile.updated_at", {
                    date: new Date(onboardingProfile.updated_at).toLocaleDateString(i18n.language)
                  })}
                </p>

                <button
                  onClick={() => navigate("/join?update=true")}
                  className="text-sm border border-white/10 px-4 py-2 rounded-lg
                             hover:bg-white/5 transition w-full text-center"
                >
                  {t("usage_profile.retake_btn")}
                </button>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-4xl mb-4">🧭</p>
                <p className="text-white/50 text-sm mb-6 whitespace-pre-line">
                  {t("usage_profile.empty.text")}
                </p>
                <button
                  onClick={() => navigate("/join?update=true")}
                  className="bg-white text-black font-semibold px-6 py-2.5
                             rounded-lg hover:bg-white/90 transition text-sm"
                >
                  {t("usage_profile.empty.cta")}
                </button>
              </div>
            )}
          </section>

          {/* ── Informations ──────────────────────────────────────────── */}
          <section>
            <h2 className="text-lg font-semibold mb-4">{t("info.title")}</h2>
            <form onSubmit={updateProfile} className="space-y-3">
              <input
                type="text" placeholder={t("info.full_name")} value={fullName}
                onChange={e => setFullName(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg
                           px-4 py-3 text-white placeholder-white/30 outline-none
                           focus:border-white/30 transition"
              />
              <button type="submit"
                      className="bg-white text-black font-semibold px-6 py-2.5
                                 rounded-lg hover:bg-white/90 transition text-sm">
                {t("info.save_btn")}
              </button>
            </form>
          </section>

          {/* ── Mot de passe ──────────────────────────────────────────── */}
          <section>
            <h2 className="text-lg font-semibold mb-4">{t("password.title")}</h2>
            <form onSubmit={changePassword} className="space-y-3">
              <input
                type="password" placeholder={t("password.current")} value={currentPwd}
                onChange={e => setCurrentPwd(e.target.value)} required
                className="w-full bg-white/5 border border-white/10 rounded-lg
                           px-4 py-3 text-white placeholder-white/30 outline-none
                           focus:border-white/30 transition"
              />
              <input
                type="password" placeholder={t("password.new")} value={newPwd}
                onChange={e => setNewPwd(e.target.value)} required
                className="w-full bg-white/5 border border-white/10 rounded-lg
                           px-4 py-3 text-white placeholder-white/30 outline-none
                           focus:border-white/30 transition"
              />
              {pwdError && <p className="text-red-400 text-sm">{pwdError}</p>}
              {pwdMsg   && <p className="text-green-400 text-sm">{pwdMsg}</p>}
              <button type="submit"
                      className="bg-white text-black font-semibold px-6 py-2.5
                                 rounded-lg hover:bg-white/90 transition text-sm">
                {t("password.submit_btn")}
              </button>
            </form>
          </section>

          {/* ── Zone dangereuse ───────────────────────────────────────── */}
          <section className="border-t border-white/10 pt-8">
            <h2 className="text-lg font-semibold mb-2 text-red-400">{t("danger.title")}</h2>
            {!showDelete ? (
              <button onClick={() => setShowDelete(true)}
                      className="text-sm text-red-400/70 hover:text-red-400
                                 transition underline">
                {t("danger.delete_btn")}
              </button>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-white/40">
                  {t("danger.confirm_text")}
                </p>
                <input
                  type="password" placeholder={t("danger.confirm_placeholder")}
                  value={deleteConfirm} onChange={e => setDeleteConfirm(e.target.value)}
                  className="w-full bg-white/5 border border-red-400/30 rounded-lg
                             px-4 py-3 text-white placeholder-white/30 outline-none
                             focus:border-red-400/50 transition"
                />
                {deleteError && <p className="text-red-400 text-sm">{deleteError}</p>}
                <div className="flex gap-3">
                  <button onClick={deleteAccount}
                          className="bg-red-500 text-white font-semibold px-6 py-2.5
                                     rounded-lg hover:bg-red-600 transition text-sm">
                    {t("danger.confirm_delete_btn")}
                  </button>
                  <button onClick={() => setShowDelete(false)}
                          className="text-white/40 hover:text-white transition text-sm">
                    {t("danger.cancel_btn")}
                  </button>
                </div>
              </div>
            )}
          </section>

        </div>
      </div>
    </>
  );
}
