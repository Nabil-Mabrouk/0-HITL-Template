import { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTranslation } from "react-i18next";

const ONBOARDING_ENABLED = import.meta.env.VITE_AUTH_CHANNEL_ONBOARDING === "true";

const roleConfig: Record<string, { labelKey: string; color: string }> = {
  admin:   { labelKey: "roles.admin",   color: "bg-red-500/20 text-red-400 border-red-500/30" },
  premium: { labelKey: "roles.premium", color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" },
  user:    { labelKey: "roles.user",    color: "bg-white/10 text-white/50 border-white/20" },
  waitlist:{ labelKey: "roles.waitlist",color: "bg-white/5 text-white/30 border-white/10" },
};

export default function Navbar() {
  const { user, logout, isAdmin } = useAuth();
  const navigate                  = useNavigate();
  const location                  = useLocation();
  const { t }                     = useTranslation("common");
  const [menuOpen, setMenuOpen]   = useState(false);
  const [scrolled, setScrolled]   = useState(false);
  const menuRef                   = useRef<HTMLDivElement>(null);

  // Effet scroll — transparent -> translucide
  useEffect(() => {
    function handleScroll() {
      setScrolled(window.scrollY > 20);
    }
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Fermer le menu si clic en dehors
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Fermer le menu à chaque changement de route
  useEffect(() => { setMenuOpen(false); }, [location.pathname]);

  const role     = user?.role ?? "";
  const rc       = roleConfig[role];
  const initials = user?.full_name
    ? user.full_name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2)
    : user?.email?.[0]?.toUpperCase() ?? "?";

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 border-b
                     transition-all duration-300
                     ${scrolled
                       ? "border-white/10 bg-black/80 backdrop-blur-sm"
                       : "border-transparent bg-transparent"
                     }`}>
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">

        {/* Logo */}
        <button
          onClick={() => navigate("/")}
          className="font-heading text-white text-xl tracking-tight
                     hover:opacity-80 transition-all duration-300 bg-clip-text 
                     text-transparent bg-gradient-to-r from-primary to-secondary"
        >
          logo
        </button>

        {/* Centre — liens de nav */}
        <div className="hidden md:flex items-center gap-6 text-sm">
          {/* Apprendre — visible pour tous */}
          <NavLink
            label={t("nav.learn")}
            active={location.pathname.startsWith("/learn")}
            onClick={() => navigate("/learn")}
          />

          {/* Liens réservés aux connectés */}
          {user && (
            <>
              <NavLink
                label={t("nav.profile")}
                active={location.pathname === "/profile"}
                onClick={() => navigate("/profile")}
              />
              {isAdmin && (
                <NavLink
                  label={t("nav.admin")}
                  active={location.pathname.startsWith("/admin")}
                  onClick={() => navigate("/admin")}
                />
              )}
              {ONBOARDING_ENABLED && (
                <NavLink
                  label={t("nav.usage_profile")}
                  active={false}
                  onClick={() => navigate("/join?update=true")}
                />
              )}
            </>
          )}

          <LangSelector />
        </div>

        {/* Droite */}
        <div className="flex items-center gap-3">

          {user ? (
            // ── Utilisateur connecté — avatar + dropdown ──────────────
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setMenuOpen(o => !o)}
                className="flex items-center gap-2 hover:opacity-80 transition"
              >
                {/* Badge rôle */}
                {rc && (
                  <span className={`hidden sm:inline-flex text-xs px-2 py-0.5
                                    rounded-full border font-medium ${rc.color}`}>
                    {t(rc.labelKey)}
                  </span>
                )}

                {/* Avatar initiales */}
                <div className="w-8 h-8 rounded-full bg-white/10 border
                                border-white/20 flex items-center justify-center
                                text-xs font-semibold text-white select-none">
                  {initials}
                </div>

                {/* Chevron */}
                <svg
                  className={`w-3 h-3 text-white/40 transition-transform duration-200
                               ${menuOpen ? "rotate-180" : ""}`}
                  fill="none" viewBox="0 0 24 24" stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round"
                        strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Dropdown menu */}
              {menuOpen && (
                <div className="absolute right-0 top-full mt-2 w-52
                                bg-zinc-900 border border-white/10 rounded-xl
                                shadow-2xl overflow-hidden">

                  {/* En-tête du dropdown */}
                  <div className="px-4 py-3 border-b border-white/10">
                    <p className="text-sm font-medium truncate">
                      {user.full_name || t("nav.profile")}
                    </p>
                    <p className="text-xs text-white/40 truncate">{user.email}</p>
                  </div>

                  {/* Items de navigation */}
                  <div className="py-1">
                    <DropdownItem
                      onClick={() => navigate("/learn")}
                      icon="📚"
                      label={t("nav.learn")}
                      active={location.pathname.startsWith("/learn")}
                    />
                    <DropdownItem
                      onClick={() => navigate("/profile")}
                      icon="👤"
                      label={t("nav.profile")}
                      active={location.pathname === "/profile"}
                    />
                    {isAdmin && (
                      <DropdownItem
                        onClick={() => navigate("/admin")}
                        icon="⚡"
                        label={t("nav.admin")}
                        active={location.pathname.startsWith("/admin")}
                      />
                    )}
                    {ONBOARDING_ENABLED && (
                      <DropdownItem
                        onClick={() => navigate("/join?update=true")}
                        icon="🧭"
                        label={t("nav.usage_profile")}
                      />
                    )}
                  </div>

                  {/* Déconnexion */}
                  <div className="border-t border-white/10 py-1">
                    <button
                      onClick={() => { logout(); navigate("/"); }}
                      className="w-full text-left px-4 py-2.5 text-sm
                                 text-red-400/80 hover:text-red-400
                                 hover:bg-white/5 transition flex items-center gap-3"
                    >
                      <span>↩</span>
                      <span>{t("nav.logout")}</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

          ) : (
            // ── Visiteur non connecté ─────────────────────────────────
            <div className="flex items-center gap-2">
              <button
                onClick={() => navigate("/login")}
                className="text-sm text-white/60 hover:text-white transition
                           px-3 py-1.5 rounded-lg hover:bg-white/5"
              >
                {t("nav.login")}
              </button>
              <button
                onClick={() => navigate("/signup")}
                className="text-sm bg-white text-black font-semibold
                           px-3 py-1.5 rounded-lg hover:bg-white/90 transition"
              >
                {t("nav.signup")}
              </button>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}

// ── Sous-composants ────────────────────────────────────────────────────────────

function NavLink({
  label, active, onClick,
}: {
  label:   string;
  active:  boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`transition ${
        active
          ? "text-white"
          : "text-white/40 hover:text-white"
      }`}
    >
      {label}
    </button>
  );
}

function DropdownItem({
  onClick, icon, label, active = false,
}: {
  onClick: () => void;
  icon:    string;
  label:   string;
  active?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-4 py-2.5 text-sm transition
                  flex items-center gap-3 hover:bg-white/5
                  ${active ? "text-white" : "text-white/60 hover:text-white"}`}
    >
      <span>{icon}</span>
      <span className="flex-1">{label}</span>
      {active && (
        <span className="w-1.5 h-1.5 rounded-full bg-white flex-shrink-0" />
      )}
    </button>
  );
}

function LangSelector() {
  const { i18n } = useTranslation();
  const langs = [
    { code: "fr", flag: "🇫🇷" },
    { code: "en", flag: "🇬🇧" },
  ];
  return (
    <div className="flex items-center gap-1">
      {langs.map(l => (
        <button
          key={l.code}
          onClick={() => i18n.changeLanguage(l.code)}
          title={l.code.toUpperCase()}
          className={`text-sm px-1.5 py-0.5 rounded transition
            ${i18n.language.startsWith(l.code)
              ? "opacity-100"
              : "opacity-30 hover:opacity-70"
            }`}
        >
          {l.flag}
        </button>
      ))}
    </div>
  );
}
