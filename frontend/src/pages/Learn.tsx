import { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTranslation } from "react-i18next";
import SEO from "../components/SEO";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface Tutorial {
  id:           number;
  title:        string;
  slug:         string;
  description:  string | null;
  cover_image:  string | null;
  access_role:  string;
  is_published: boolean;
  is_featured:  boolean;
  lang:         string;
  tags:         string[];
  views_count:  number;
  lessons:      { id: number; duration_minutes: number | null }[];
}

// ── Helpers ────────────────────────────────────────────────────────────────

function getImgUrl(path: string | null): string | null {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  return `${API}${path}`;
}

function totalMinutes(tut: Tutorial): number {
  return tut.lessons.reduce((acc, l) => acc + (l.duration_minutes ?? 0), 0);
}

function isLocked(tut: Tutorial, user: any): boolean {
  return tut.access_role === "premium" &&
    (!user || !["premium", "admin"].includes(user.role));
}

// ── Card tutoriel ──────────────────────────────────────────────────────────

function TutorialCard({
  tut, onClick,
}: {
  tut:     Tutorial;
  onClick: () => void;
}) {
  const { t }    = useTranslation("learn");
  const { user } = useAuth();
  
  const premium  = tut.access_role === "premium";
  const locked   = isLocked(tut, user);
  const mins     = totalMinutes(tut);

  return (
    <button
      onClick={onClick}
      className="text-left border border-white/10 rounded-2xl overflow-hidden
                 hover:border-white/30 hover:bg-white/5 transition group
                 flex flex-col"
    >
      {/* Cover */}
      {tut.cover_image ? (
        <img
          src={getImgUrl(tut.cover_image) || ""}
          alt={tut.title}
          className="w-full h-40 object-cover opacity-80
                     group-hover:opacity-100 transition"
        />
      ) : (
        <div className="w-full h-40 bg-white/5 flex items-center
                        justify-center text-4xl">
          📚
        </div>
      )}

      <div className="p-5 flex flex-col flex-1">
        {/* Badges */}
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          {tut.access_role === "admin" ? (
            <span className="text-xs px-2 py-0.5 rounded-full
                             bg-red-500/20 text-red-400
                             border border-red-500/30">
              🔒 Interne
            </span>
          ) : premium ? (
            <span className="text-xs px-2 py-0.5 rounded-full
                             bg-yellow-500/20 text-yellow-400
                             border border-yellow-500/30">
              ⭐ {t("catalogue.premium")}
            </span>
          ) : (
            <span className="text-xs px-2 py-0.5 rounded-full
                             bg-white/10 text-white/50 border border-white/20">
              {t("catalogue.free")}
            </span>
          )}
          {locked && <span className="text-xs text-white/30">🔒</span>}
          {tut.is_featured && (
            <span className="text-xs px-2 py-0.5 rounded-full
                             bg-indigo-500/20 text-indigo-400
                             border border-indigo-500/30">
              ✦ En avant
            </span>
          )}
        </div>

        {/* Titre */}
        <h2 className="text-base font-semibold mb-2
                       group-hover:text-white transition line-clamp-2">
          {tut.title}
        </h2>

        {/* Description */}
        {tut.description && (
          <p className="text-white/40 text-sm mb-3 line-clamp-2 flex-1">
            {tut.description}
          </p>
        )}

        {/* Tags */}
        {tut.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {tut.tags.slice(0, 4).map(tag => (
              <span key={tag}
                    className="text-xs px-2 py-0.5 rounded-full
                               bg-white/5 text-white/40 border border-white/10">
                {tag}
              </span>
            ))}
          </div>
        )}

        {/* Méta */}
        <div className="flex items-center gap-3 text-xs text-white/25 mt-auto">
          <span>
            {t("catalogue.lessons", { count: tut.lessons.length })}
          </span>
          {mins > 0 && <span>{mins} min</span>}
          {tut.views_count > 0 && (
            <span className="ml-auto">{tut.views_count} vues</span>
          )}
        </div>
      </div>
    </button>
  );
}

// ── Card featured (grande) ─────────────────────────────────────────────────

function FeaturedCard({
  tut, onClick,
}: {
  tut:     Tutorial;
  onClick: () => void;
}) {
  const { t }    = useTranslation("learn");
  const { user } = useAuth();
  
  const locked   = isLocked(tut, user);
  const mins     = totalMinutes(tut);

  return (
    <button
      onClick={onClick}
      className="w-full text-left border border-indigo-500/30 rounded-2xl
                 overflow-hidden hover:border-indigo-500/60 transition group
                 bg-indigo-500/5 flex flex-col md:flex-row"
    >
      {/* Cover grande */}
      {tut.cover_image ? (
        <img
          src={getImgUrl(tut.cover_image) || ""}
          alt={tut.title}
          className="w-full md:w-72 h-48 md:h-auto object-cover
                     opacity-80 group-hover:opacity-100 transition flex-shrink-0"
        />
      ) : (
        <div className="w-full md:w-72 h-48 bg-indigo-500/10 flex items-center
                        justify-center text-6xl flex-shrink-0">
          📚
        </div>
      )}

      <div className="p-6 flex flex-col justify-center flex-1">
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <span className="text-xs px-2 py-0.5 rounded-full
                           bg-indigo-500/20 text-indigo-400
                           border border-indigo-500/30">
            ✦ Mis en avant
          </span>
          {tut.access_role === "admin" ? (
            <span className="text-xs px-2 py-0.5 rounded-full
                             bg-red-500/20 text-red-400
                             border border-red-500/30">
              🔒 Interne
            </span>
          ) : tut.access_role === "premium" ? (
            <span className="text-xs px-2 py-0.5 rounded-full
                             bg-yellow-500/20 text-yellow-400
                             border border-yellow-500/30">
              ⭐ {t("catalogue.premium")}
            </span>
          ) : (
            <span className="text-xs px-2 py-0.5 rounded-full
                             bg-white/10 text-white/50 border border-white/20">
              {t("catalogue.free")}
            </span>
          )}
          {locked && <span className="text-xs text-white/30">🔒</span>}
        </div>

        <h2 className="text-xl font-bold mb-3 group-hover:text-indigo-300
                       transition">
          {tut.title}
        </h2>

        {tut.description && (
          <p className="text-white/50 text-sm mb-4 line-clamp-3">
            {tut.description}
          </p>
        )}

        {tut.tags?.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-4">
            {tut.tags.map(tag => (
              <span key={tag}
                    className="text-xs px-2 py-0.5 rounded-full
                               bg-white/5 text-white/40 border border-white/10">
                {tag}
              </span>
            ))}
          </div>
        )}

        <div className="flex items-center gap-4 text-xs text-white/30">
          <span>{t("catalogue.lessons", { count: tut.lessons.length })}</span>
          {mins > 0 && <span>{mins} min</span>}
          {tut.views_count > 0 && <span>{tut.views_count} vues</span>}
        </div>
      </div>
    </button>
  );
}

// ── Section titre ──────────────────────────────────────────────────────────

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h2 className="text-lg font-semibold text-white/70 mb-4 flex items-center gap-2">
      {children}
    </h2>
  );
}

// ── Page principale ────────────────────────────────────────────────────────

export default function Learn() {
  const { t, i18n }               = useTranslation("learn");
  const [tutorials, setTutorials] = useState<Tutorial[]>([]);
  const [loading, setLoading]     = useState(true);
  
  const navigate                  = useNavigate();

  // ── Filtres et recherche
  const [search, setSearch]     = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [sortBy, setSortBy]     = useState<"recent" | "popular">("recent");
  const [accessFilter, setAccessFilter] = useState<"" | "free" | "premium" | "admin">("");

  useEffect(() => {
    setLoading(true);
    const lang = i18n.language.split("-")[0];
    const headers: Record<string, string> = {};
    // Envoyer le token si connecté pour voir les premium
    const token = localStorage.getItem("access_token") ||
                  sessionStorage.getItem("access_token");
    if (token) headers["Authorization"] = `Bearer ${token}`;

    fetch(`${API}/api/content/tutorials?lang=${lang}`, { headers })
      .then(r => r.json())
      .then(data => Array.isArray(data) ? setTutorials(data) : setTutorials([]))
      .catch(() => setTutorials([]))
      .finally(() => setLoading(false));
  }, [i18n.language]);

  // ── Tous les tags disponibles (dédoublonnés)
  const allTags = useMemo(() => {
    const tags = new Set<string>();
    tutorials.forEach(t => t.tags?.forEach(tag => tags.add(tag)));
    return Array.from(tags).sort();
  }, [tutorials]);

  // ── Tutoriaux filtrés et triés
  const filtered = useMemo(() => {
    let list = [...tutorials];

    // Filtre recherche
    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(t =>
        t.title.toLowerCase().includes(q) ||
        t.description?.toLowerCase().includes(q) ||
        t.tags?.some(tag => tag.toLowerCase().includes(q))
      );
    }

    // Filtre tag
    if (tagFilter) {
      list = list.filter(t => t.tags?.includes(tagFilter));
    }

    // Filtre accès
    if (accessFilter === "free") {
      list = list.filter(t => t.access_role === "user");
    } else if (accessFilter === "premium") {
      list = list.filter(t => t.access_role === "premium");
    } else if (accessFilter === "admin") {
      list = list.filter(t => t.access_role === "admin");
    }

    // Tri
    if (sortBy === "popular") {
      list.sort((a, b) => (b.views_count ?? 0) - (a.views_count ?? 0));
    } else {
      list.sort((a, b) =>
        new Date(b.id).getTime() - new Date(a.id).getTime()
      );
    }

    return list;
  }, [tutorials, search, tagFilter, sortBy, accessFilter]);

  // ── Sections spéciales (sans filtres actifs)
  const hasActiveFilter = search || tagFilter || accessFilter;
  const featured  = tutorials.find(t => t.is_featured);
  const recent    = tutorials
    .filter(t => !t.is_featured)
    .slice(0, 4);
  const popular   = [...tutorials]
    .sort((a, b) => (b.views_count ?? 0) - (a.views_count ?? 0))
    .filter(t => !t.is_featured)
    .slice(0, 4);

  const hasFilters = allTags.length > 0 || tutorials.length > 3;

  return (
    <>
      <SEO
        title={t("catalogue.title")}
        description={t("catalogue.subtitle")}
        url="/learn"
      />
      <div className="min-h-screen bg-black text-white">
        <div className="max-w-6xl mx-auto px-6 py-16">

          {/* ── En-tête ──────────────────────────────────────────────── */}
          <h1 className="text-4xl font-bold mb-3">{t("catalogue.title")}</h1>
          <p className="text-white/40 mb-10">{t("catalogue.subtitle")}</p>

          {loading ? (
            <p className="text-white/30">{t("catalogue.loading")}</p>
          ) : tutorials.length === 0 ? (
            <p className="text-white/30">{t("catalogue.empty")}</p>
          ) : (
            <div className="space-y-14">

              {/* ── Barre de recherche + filtres ─────────────────────── */}
              {hasFilters && (
                <div className="flex flex-wrap gap-3 items-center">
                  {/* Recherche */}
                  <div className="relative flex-1 min-w-48">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2
                                     text-white/30 text-sm">🔍</span>
                    <input
                      type="text"
                      placeholder="Rechercher un tutorial..."
                      value={search}
                      onChange={e => setSearch(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-xl
                                 pl-9 pr-4 py-2.5 text-sm text-white
                                 placeholder-white/25 outline-none
                                 focus:border-white/30 transition"
                    />
                    {search && (
                      <button
                        onClick={() => setSearch("")}
                        className="absolute right-3 top-1/2 -translate-y-1/2
                                   text-white/30 hover:text-white transition text-xs"
                      >
                        ✕
                      </button>
                    )}
                  </div>

                  {/* Filtre tag */}
                  {allTags.length > 0 && (
                    <select
                      value={tagFilter}
                      onChange={e => setTagFilter(e.target.value)}
                      className="bg-white/5 border border-white/10 rounded-xl
                                 px-3 py-2.5 text-sm text-white outline-none
                                 focus:border-white/30 transition"
                    >
                      <option value="">Tous les tags</option>
                      {allTags.map(tag => (
                        <option key={tag} value={tag}>{tag}</option>
                      ))}
                    </select>
                  )}

                  {/* Filtre accès */}
                  <select
                    value={accessFilter}
                    onChange={e => setAccessFilter(
                      e.target.value as "" | "free" | "premium" | "admin"
                    )}
                    className="bg-white/5 border border-white/10 rounded-xl
                               px-3 py-2.5 text-sm text-white outline-none
                               focus:border-white/30 transition"
                  >
                    <option value="">Tous les accès</option>
                    <option value="free">Gratuit</option>
                    <option value="premium">⭐ Premium</option>
                    <option value="admin">🔒 Interne</option>
                  </select>

                  {/* Tri */}
                  <div className="flex gap-1 ml-auto">
                    {([
                      { key: "recent",  label: "Récents"   },
                      { key: "popular", label: "Populaires" },
                    ] as const).map(s => (
                      <button
                        key={s.key}
                        onClick={() => setSortBy(s.key)}
                        className={`text-xs px-3 py-2 rounded-lg border transition
                          ${sortBy === s.key
                            ? "border-white/40 text-white bg-white/10"
                            : "border-white/10 text-white/40 hover:text-white"
                          }`}
                      >
                        {s.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* ── Mode filtré : grille plate ────────────────────────── */}
              {hasActiveFilter ? (
                <div>
                  {filtered.length === 0 ? (
                    <div className="text-center py-16">
                      <p className="text-4xl mb-4">🔍</p>
                      <p className="text-white/30">
                        Aucun tutorial ne correspond à votre recherche.
                      </p>
                      <button
                        onClick={() => {
                          setSearch(""); setTagFilter("");
                          setAccessFilter("");
                        }}
                        className="mt-4 text-sm text-indigo-400
                                   hover:text-indigo-300 transition"
                      >
                        Réinitialiser les filtres
                      </button>
                    </div>
                  ) : (
                    <>
                      <p className="text-sm text-white/30 mb-4">
                        {filtered.length} tutorial{filtered.length > 1 ? "s" : ""}
                      </p>
                      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
                        {filtered.map(tut => (
                          <TutorialCard
                            key={tut.id}
                            tut={tut}
                            onClick={() => navigate(`/learn/${tut.slug}`)}
                          />
                        ))}
                      </div>
                    </>
                  )}
                </div>
              ) : (
                /* ── Mode normal : sections ───────────────────────────── */
                <>
                  {/* Featured */}
                  {featured && (
                    <section>
                      <SectionTitle>✦ À la une</SectionTitle>
                      <FeaturedCard
                        tut={featured}
                        onClick={() => navigate(`/learn/${featured.slug}`)}
                      />
                    </section>
                  )}

                  {/* Derniers ajoutés */}
                  {recent.length > 0 && (
                    <section>
                      <SectionTitle>🆕 Derniers ajoutés</SectionTitle>
                      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
                        {recent.map(tut => (
                          <TutorialCard
                            key={tut.id}
                            tut={tut}
                            onClick={() => navigate(`/learn/${tut.slug}`)}
                          />
                        ))}
                      </div>
                    </section>
                  )}

                  {/* Populaires */}
                  {popular.length > 0 &&
                   popular.some(t => t.views_count > 0) && (
                    <section>
                      <SectionTitle>🔥 Populaires</SectionTitle>
                      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
                        {popular.map(tut => (
                          <TutorialCard
                            key={tut.id}
                            tut={tut}
                            onClick={() => navigate(`/learn/${tut.slug}`)}
                          />
                        ))}
                      </div>
                    </section>
                  )}

                  {/* Tous les tutoriaux */}
                  <section>
                    <div className="flex items-center justify-between mb-4">
                      <SectionTitle>📚 Tous les tutoriaux</SectionTitle>
                      <p className="text-sm text-white/30">
                        {tutorials.length} tutorial{tutorials.length > 1 ? "s" : ""}
                      </p>
                    </div>
                    <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
                      {tutorials.map(tut => (
                        <TutorialCard
                          key={tut.id}
                          tut={tut}
                          onClick={() => navigate(`/learn/${tut.slug}`)}
                        />
                      ))}
                    </div>
                  </section>
                </>
              )}

              {/* ── Tags populaires (en bas, mode normal) ─────────────── */}
              {!hasActiveFilter && allTags.length > 0 && (
                <section>
                  <SectionTitle>🏷️ Parcourir par tag</SectionTitle>
                  <div className="flex flex-wrap gap-2">
                    {allTags.map(tag => (
                      <button
                        key={tag}
                        onClick={() => setTagFilter(tag)}
                        className="text-sm px-3 py-1.5 rounded-full border
                                   border-white/10 text-white/50
                                   hover:border-white/30 hover:text-white
                                   transition"
                      >
                        {tag}
                      </button>
                    ))}
                  </div>
                </section>
              )}

            </div>
          )}
        </div>
      </div>
    </>
  );
}
