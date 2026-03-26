import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useNavigate } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import WorldMap       from "@/components/analytics/WorldMap";
import VisitsTimeline from "@/components/analytics/VisitsTimeline";
import { useTranslation } from "react-i18next";
import SEO from "@/components/SEO";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// ── Types ──────────────────────────────────────────────────────────────────

interface Stats {
  total_users:      number;
  active_users:     number;
  verified_users:   number;
  premium_users:    number;
  waitlist_total:   number;
  waitlist_pending: number;
}
interface UserRow {
  id: number; email: string; full_name: string | null;
  role: string; is_active: boolean; created_at: string;
}
interface WaitlistEntry {
  id: number; email: string; created_at: string; invited_at: string | null;
}
interface CountryData {
  country_code: string; country_name: string; visits: number; pct: number;
}
interface CityData {
  city: string; country_code: string;
  latitude: number; longitude: number; visits: number;
}
interface TimelinePoint { date: string; visits: number; }
interface TutorialAdmin {
  id: number; title: string; slug: string;
  cover_image: string | null;
  access_role: string; is_published: boolean;
  lang: string;
  lessons: { id: number }[];
}
interface DbStats {
  counts:         Record<string, number>;
  db_size:        string;
  table_sizes:    Record<string, string>;
  last_migration: string;
  settings: {
    tokens_retention_days: number;
    visits_retention_days: number;
    logs_retention_days:   number;
    cleanup_frequency:     string;
    last_cleanup_at:       string | null;
  };
}

type Tab = "users" | "waitlist" | "analytics" | "content" | "database" | "security";

interface SecurityEvent {
  id: number; event_type: string; severity: string;
  ip_address: string; path: string; method: string;
  user_agent: string; details: Record<string, string> | null;
  created_at: string;
}
interface SecuritySummary {
  total: number; last_24h: number;
  by_severity: Record<string, number>;
  by_type:     Record<string, number>;
  top_ips:     { ip: string; hits: number }[];
}

// ── Composant ──────────────────────────────────────────────────────────────

export default function AdminDashboard() {
  const { accessToken, isAdmin, isLoading } = useAuth();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation("admin");

  // ── Onglets
  const [activeTab, setActiveTab] = useState<Tab>("users");

  // ── Users
  const [stats, setStats]             = useState<Stats | null>(null);
  const [users, setUsers]             = useState<UserRow[]>([]);
  const [total, setTotal]             = useState(0);
  const [search, setSearch]           = useState("");
  const [page, setPage]               = useState(1);
  const [showDeleted, setShowDeleted] = useState(false);
  const [roleFilter, setRoleFilter]   = useState("");

  // ── Waitlist
  const [waitlist, setWaitlist] = useState<WaitlistEntry[]>([]);

  // ── Analytics
  const [worldCountries, setWorldCountries] = useState<CountryData[]>([]);
  const [worldCities, setWorldCities]       = useState<CityData[]>([]);
  const [timeline, setTimeline]             = useState<TimelinePoint[]>([]);
  const [topCountries, setTopCountries]     = useState<CountryData[]>([]);
  const [analyticsRole, setAnalyticsRole]   = useState("");
  const [analyticsDays, setAnalyticsDays]   = useState(30);
  const [analyticsTotal, setAnalyticsTotal] = useState(0);

  // ── Content
  const [tutorials, setTutorials]               = useState<TutorialAdmin[]>([]);
  const [showTutorialForm, setShowTutorialForm] = useState(false);
  const [tTitle, setTTitle]                     = useState("");
  const [tDesc, setTDesc]                       = useState("");
  const [tRole, setTRole]                       = useState("user");
  const [tLang, setTLang]                       = useState("fr");
  const [tPublished, setTPublished]             = useState(false);
  // Import ZIP
  const [importing, setImporting]       = useState(false);
  const [importMsg, setImportMsg]       = useState("");
  const importInputRef                  = useRef<HTMLInputElement>(null);

  // ── Database (chapitre 8)
  const [dbStats, setDbStats]                     = useState<DbStats | null>(null);
  const [dbLoading, setDbLoading]                 = useState(false);
  const [cleanupRunning, setCleanupRunning]       = useState(false);
  const [vacuumRunning, setVacuumRunning]         = useState(false);
  const [tokensDays, setTokensDays]               = useState(30);
  const [visitsDays, setVisitsDays]               = useState(90);
  const [logsDays, setLogsDays]                   = useState(180);
  const [frequency, setFrequency]                 = useState("weekly");
  const [importUsersResult, setImportUsersResult] = useState("");
  const importUsersRef                            = useRef<HTMLInputElement>(null);

  // ── Security
  const [secEvents,  setSecEvents]  = useState<SecurityEvent[]>([]);
  const [secSummary, setSecSummary] = useState<SecuritySummary | null>(null);
  const [secDays,    setSecDays]    = useState(7);
  const [secLoading, setSecLoading] = useState(false);

  // ── Flash message
  const [actionMsg, setActionMsg] = useState("");

  // ── Guards ────────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!isLoading && !isAdmin) navigate("/");
  }, [isAdmin, isLoading, navigate]);

  useEffect(() => {
    if (!isAdmin) return;
    fetchStats();
    if (activeTab === "users")     fetchUsers();
    if (activeTab === "waitlist")  fetchWaitlist();
    if (activeTab === "analytics") fetchAnalytics();
    if (activeTab === "content")   fetchTutorials();
    if (activeTab === "database")  fetchDbStats();
    if (activeTab === "security")  fetchSecurity();
  }, [isAdmin, activeTab, page, search, showDeleted, roleFilter]);

  // ── API helper ────────────────────────────────────────────────────────────
  async function apiFetch(path: string, options?: RequestInit) {
    return fetch(`${API}/api${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization:  `Bearer ${accessToken}`,
        ...(options?.headers ?? {}),
      },
    });
  }

  function showMsg(msg: string) {
    setActionMsg(msg);
    setTimeout(() => setActionMsg(""), 3000);
  }

  // ── Fetch ─────────────────────────────────────────────────────────────────
  async function fetchStats() {
    const res = await apiFetch("/admin/stats");
    if (res.ok) setStats(await res.json());
  }

  async function fetchUsers() {
    const params = new URLSearchParams({
      page: String(page), per_page: "20",
      search, show_deleted: String(showDeleted),
    });
    if (roleFilter) params.set("role", roleFilter);
    const res = await apiFetch(`/admin/users?${params}`);
    if (res.ok) {
      const data = await res.json();
      setUsers(data.users);
      setTotal(data.total);
    }
  }

  async function fetchWaitlist() {
    const params = new URLSearchParams({ page: String(page), per_page: "20" });
    const res = await apiFetch(`/admin/waitlist?${params}`);
    if (res.ok) {
      const data = await res.json();
      setWaitlist(data.entries);
      setTotal(data.total);
    }
  }

  async function fetchAnalytics() {
    const params = new URLSearchParams({ days: String(analyticsDays) });
    if (analyticsRole) params.set("role", analyticsRole);
    const [worldRes, timelineRes, topRes] = await Promise.all([
      apiFetch(`/admin/analytics/world?${params}`),
      apiFetch(`/admin/analytics/timeline?${params}`),
      apiFetch(`/admin/analytics/top-countries?${params}`),
    ]);
    if (worldRes.ok) {
      const d = await worldRes.json();
      setWorldCountries(d.countries);
      setWorldCities(d.cities);
      setAnalyticsTotal(d.total);
    }
    if (timelineRes.ok) setTimeline((await timelineRes.json()).data);
    if (topRes.ok)      setTopCountries((await topRes.json()).data);
  }

  async function fetchTutorials() {
    const res = await apiFetch("/admin/content/tutorials");
    if (res.ok) setTutorials((await res.json()).tutorials ?? []);
  }

  async function fetchSecurity() {
    setSecLoading(true);
    const [evtRes, sumRes] = await Promise.all([
      apiFetch(`/admin/security/events?days=${secDays}&per_page=100`),
      apiFetch(`/admin/security/summary?days=${secDays}`),
    ]);
    if (evtRes.ok) setSecEvents((await evtRes.json()).events ?? []);
    if (sumRes.ok) setSecSummary(await sumRes.json());
    setSecLoading(false);
  }

  async function fetchDbStats() {
    setDbLoading(true);
    const res = await apiFetch("/admin/db/stats");
    if (res.ok) {
      const data = await res.json();
      setDbStats(data);
      setTokensDays(data.settings.tokens_retention_days);
      setVisitsDays(data.settings.visits_retention_days);
      setLogsDays(data.settings.logs_retention_days);
      setFrequency(data.settings.cleanup_frequency);
    }
    setDbLoading(false);
  }

  // ── Actions users ─────────────────────────────────────────────────────────
  async function updateRole(userId: number, role: string) {
    await apiFetch(`/admin/users/${userId}/role`, {
      method: "PUT", body: JSON.stringify({ role }),
    });
    fetchUsers(); fetchStats();
  }

  async function toggleSuspend(userId: number) {
    await apiFetch(`/admin/users/${userId}/suspend`, { method: "PUT" });
    fetchUsers(); fetchStats();
  }

  // ── Actions waitlist ──────────────────────────────────────────────────────
  async function invite(id: number) {
    const res = await apiFetch(`/admin/waitlist/${id}/invite`, { method: "POST" });
    showMsg((await res.json()).message ?? "Invitation envoyée");
    fetchWaitlist(); fetchStats();
  }

  async function reinvite(id: number) {
    const res = await apiFetch(`/admin/waitlist/${id}/reinvite`, { method: "POST" });
    showMsg((await res.json()).message ?? "Invitation renvoyée");
    fetchWaitlist();
  }

  // ── Actions content ───────────────────────────────────────────────────────
  async function createTutorial() {
    if (!tTitle.trim()) return;
    const res = await apiFetch("/admin/content/tutorials", {
      method: "POST",
      body: JSON.stringify({
        title:        tTitle,
        description:  tDesc,
        access_role:  tRole,
        lang:         tLang,
        is_published: tPublished,
      }),
    });
    if (res.ok) {
      const data = await res.json();
      showMsg(t("content.tutorials.flash_created"));
      setShowTutorialForm(false);
      setTTitle(""); setTDesc(""); setTRole("user"); setTPublished(false);
      navigate(`/admin/content/${data.id}`);
    }
  }

  async function togglePublishTutorial(id: number, current: boolean) {
    await apiFetch(`/admin/content/tutorials/${id}`, {
      method: "PUT",
      body: JSON.stringify({ is_published: !current }),
    });
    fetchTutorials();
  }

  async function updateAccessRole(id: number, access_role: string) {
    await apiFetch(`/admin/content/tutorials/${id}`, {
      method: "PUT",
      body: JSON.stringify({ access_role }),
    });
    fetchTutorials();
  }

  async function deleteTutorial(id: number) {
    if (!confirm(t("content.tutorials.actions.delete_confirm"))) return;
    await apiFetch(`/admin/content/tutorials/${id}`, { method: "DELETE" });
    fetchTutorials();
  }

  async function handleImportTutorial(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setImportMsg("");
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API}/api/admin/content/tutorials/import`, {
      method:  "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
      body:    form,
    });
    const data = await res.json();
    setImportMsg(res.ok
      ? `✓ ${data.message}`
      : `✗ ${data.detail ?? "Erreur"}`
    );
    setImporting(false);
    if (importInputRef.current) importInputRef.current.value = "";
    if (res.ok) fetchTutorials();
  }

  // ── Actions database (chapitre 8) ─────────────────────────────────────────
  async function saveDbSettings() {
    const res = await apiFetch("/admin/db/settings", {
      method: "PUT",
      body: JSON.stringify({
        tokens_retention_days: tokensDays,
        visits_retention_days: visitsDays,
        logs_retention_days:   logsDays,
        cleanup_frequency:     frequency,
      }),
    });
    if (res.ok) { showMsg("Paramètres sauvegardés ✓"); fetchDbStats(); }
  }

  async function runCleanup() {
    setCleanupRunning(true);
    const res = await apiFetch("/admin/db/cleanup", { method: "POST" });
    if (res.ok) {
      const d = await res.json();
      showMsg(
        `Nettoyage terminé — ${d.total_deleted} lignes supprimées ` +
        `(tokens: ${d.tokens_deleted}, visites: ${d.visits_deleted}, ` +
        `logs: ${d.logs_deleted})`
      );
      fetchDbStats();
    }
    setCleanupRunning(false);
  }

  async function runVacuum() {
    setVacuumRunning(true);
    const res = await apiFetch("/admin/db/vacuum", { method: "POST" });
    if (res.ok) showMsg("VACUUM ANALYZE terminé ✓");
    setVacuumRunning(false);
  }

  async function exportUsers() {
    const res = await fetch(`${API}/api/admin/db/export/users`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (res.ok) {
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = `users-export-${new Date().toISOString().slice(0, 10)}.zip`;
      a.click();
      URL.revokeObjectURL(url);
    }
  }

  async function exportTutorialsBulk() {
    const res = await fetch(`${API}/api/admin/db/export/tutorials/bulk`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (res.ok) {
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = `tutorials-bulk-${new Date().toISOString().slice(0, 10)}.zip`;
      a.click();
      URL.revokeObjectURL(url);
    }
  }

  async function exportTutorial(id: number, slug: string) {
    const res = await fetch(`${API}/api/admin/db/export/tutorial/${id}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (res.ok) {
      const blob = await res.blob();
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement("a");
      a.href     = url;
      a.download = `${slug}.zip`;
      a.click();
      URL.revokeObjectURL(url);
    }
  }

  async function handleImportUsers(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API}/api/admin/db/import/users`, {
      method:  "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
      body:    form,
    });
    const data = await res.json();
    setImportUsersResult(res.ok
      ? `✓ ${data.message}`
      : `✗ ${data.detail ?? "Erreur"}`
    );
    if (importUsersRef.current) importUsersRef.current.value = "";
  }

  // ── UI helpers ────────────────────────────────────────────────────────────
  const isDeleted = (email: string) =>
    email.startsWith("deleted_") && email.endsWith("@deleted.invalid");

  const roleColors: Record<string, string> = {
    admin:    "bg-red-100 text-red-800",
    premium:  "bg-yellow-100 text-yellow-800",
    user:     "bg-blue-100 text-blue-800",
    waitlist: "bg-gray-100 text-gray-800",
  };

  // ── Loading guard ─────────────────────────────────────────────────────────
  if (isLoading || !stats) return (
    <div className="flex items-center justify-center min-h-screen">
      {t("common.loading")}
    </div>
  );

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <>
      <SEO title={t("title")} noindex={true} />
      <div className="max-w-7xl mx-auto px-6 py-8">

        {/* Flash */}
        {actionMsg && (
          <div className="mb-4 px-4 py-2 bg-green-50 border border-green-200
                          text-green-800 rounded-lg text-sm">
            {actionMsg}
          </div>
        )}

        <h1 className="text-3xl font-bold mb-8">{t("title")}</h1>

        {/* ── Stats ──────────────────────────────────────────────────────── */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          {[
            { key: "total_users",      value: stats.total_users },
            { key: "active_users",     value: stats.active_users },
            { key: "verified_users",   value: stats.verified_users },
            { key: "premium_users",    value: stats.premium_users },
            { key: "waitlist_total",   value: stats.waitlist_total },
            { key: "waitlist_pending", value: stats.waitlist_pending },
          ].map(s => (
            <Card key={s.key}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">
                  {t(`stats.${s.key}`)}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold">{s.value}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* ── Tabs ───────────────────────────────────────────────────────── */}
        <div className="flex gap-4 mb-6 border-b">
          {([
            { key: "users",     label: t("tabs.users")     },
            { key: "waitlist",  label: t("tabs.waitlist")  },
            { key: "analytics", label: t("tabs.analytics") },
            { key: "content",   label: t("tabs.content")   },
            { key: "database",  label: "Base de données"   },
            { key: "security",  label: "🔐 Sécurité"        },
          ] as { key: Tab; label: string }[]).map(tabItem => (
            <button
              key={tabItem.key}
              onClick={() => { setActiveTab(tabItem.key); setPage(1); setSearch(""); }}
              className={`pb-3 px-2 text-sm font-medium transition border-b-2 -mb-px
                ${activeTab === tabItem.key
                  ? "border-foreground text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
                }`}
            >
              {tabItem.label}
            </button>
          ))}
        </div>

        {/* ── Tab : Utilisateurs ─────────────────────────────────────────── */}
        {activeTab === "users" && (
          <>
            <div className="flex flex-wrap gap-3 mb-4 items-center">
              <Input
                placeholder={t("users.search_placeholder")}
                value={search}
                onChange={e => { setSearch(e.target.value); setPage(1); }}
                className="max-w-xs"
              />
              <select
                value={roleFilter}
                onChange={e => { setRoleFilter(e.target.value); setPage(1); }}
                className="text-sm border rounded-lg px-3 py-2 bg-background text-foreground"
              >
                <option value="">{t("users.filter_all_roles")}</option>
                {["user", "premium", "admin", "waitlist"].map(r => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>
              <label className="flex items-center gap-2 text-sm text-muted-foreground
                                cursor-pointer select-none ml-auto">
                <input
                  type="checkbox" checked={showDeleted}
                  onChange={e => { setShowDeleted(e.target.checked); setPage(1); }}
                  className="rounded"
                />
                {t("users.show_deleted")}
              </label>
            </div>

            <Card>
              <CardContent className="p-0">
                <table className="w-full text-sm">
                  <thead className="border-b bg-muted/50">
                    <tr>
                      {["id", "email", "name", "role", "status", "joined", "actions"].map(h => (
                        <th key={h} className="px-4 py-3 text-left font-medium
                                               text-muted-foreground">
                          {t(`users.table.${h}`)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {users.map(u => {
                      const deleted = isDeleted(u.email);
                      return (
                        <tr key={u.id} className={`border-b transition ${
                          deleted ? "opacity-40 bg-red-500/5" : "hover:bg-muted/30"
                        }`}>
                          <td className="px-4 py-3 text-muted-foreground">{u.id}</td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              {u.email}
                              {deleted && (
                                <span className="text-xs text-red-400 border
                                                border-red-400/30 rounded px-1">
                                  {t("users.status.deleted")}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-4 py-3">{u.full_name ?? "—"}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 rounded text-xs font-medium
                              ${roleColors[u.role] ?? ""}`}>
                              {u.role}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <Badge variant={u.is_active ? "default" : "destructive"}>
                              {u.is_active
                                ? t("users.status.active")
                                : t("users.status.suspended")}
                            </Badge>
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {new Date(u.created_at).toLocaleDateString(i18n.language)}
                          </td>
                          <td className="px-4 py-3">
                            {!deleted && (
                              <div className="flex gap-2 items-center">
                                <select
                                  value={u.role}
                                  onChange={e => updateRole(u.id, e.target.value)}
                                  className="text-xs border rounded px-1 py-1 bg-background"
                                >
                                  {["user", "premium", "admin", "waitlist"].map(r => (
                                    <option key={r} value={r}>{r}</option>
                                  ))}
                                </select>
                                <Button size="sm" variant="outline"
                                        onClick={() => toggleSuspend(u.id)}>
                                  {u.is_active
                                    ? t("users.actions.suspend")
                                    : t("users.actions.activate")}
                                </Button>
                              </div>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                    {users.length === 0 && (
                      <tr>
                        <td colSpan={7}
                            className="px-4 py-8 text-center text-muted-foreground">
                          {t("users.empty")}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </CardContent>
            </Card>

            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-muted-foreground">
                {t("users.count", { count: total, count_plural: t("users.count_plural") })}
              </p>
              <div className="flex gap-2">
                <Button size="sm" variant="outline"
                        disabled={page === 1}
                        onClick={() => setPage(p => p - 1)}>
                  {t("common.prev")}
                </Button>
                <Button size="sm" variant="outline"
                        disabled={page * 20 >= total}
                        onClick={() => setPage(p => p + 1)}>
                  {t("common.next")}
                </Button>
              </div>
            </div>
          </>
        )}

        {/* ── Tab : Waitlist ─────────────────────────────────────────────── */}
        {activeTab === "waitlist" && (
          <>
            <Card>
              <CardContent className="p-0">
                <table className="w-full text-sm">
                  <thead className="border-b bg-muted/50">
                    <tr>
                      {["id", "email", "joined", "status", "invited_at", "actions"].map(h => (
                        <th key={h} className="px-4 py-3 text-left font-medium
                                               text-muted-foreground">
                          {t(`waitlist.table.${h}`)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {waitlist.map(e => (
                      <tr key={e.id} className="border-b hover:bg-muted/30 transition">
                        <td className="px-4 py-3 text-muted-foreground">{e.id}</td>
                        <td className="px-4 py-3">{e.email}</td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {new Date(e.created_at).toLocaleDateString(i18n.language)}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant={e.invited_at ? "default" : "secondary"}>
                            {e.invited_at
                              ? t("waitlist.status.invited")
                              : t("waitlist.status.pending")}
                          </Badge>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {e.invited_at
                            ? new Date(e.invited_at).toLocaleDateString(i18n.language)
                            : "—"}
                        </td>
                        <td className="px-4 py-3">
                          {!e.invited_at ? (
                            <Button size="sm" onClick={() => invite(e.id)}>
                              {t("waitlist.actions.invite")}
                            </Button>
                          ) : (
                            <Button size="sm" variant="outline"
                                    onClick={() => reinvite(e.id)}>
                              {t("waitlist.actions.reinvite")}
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                    {waitlist.length === 0 && (
                      <tr>
                        <td colSpan={6}
                            className="px-4 py-8 text-center text-muted-foreground">
                          {t("waitlist.empty")}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </CardContent>
            </Card>

            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-muted-foreground">
                {t("waitlist.count", { count: total, count_plural: t("waitlist.count_plural") })}
              </p>
              <div className="flex gap-2">
                <Button size="sm" variant="outline"
                        disabled={page === 1}
                        onClick={() => setPage(p => p - 1)}>
                  {t("common.prev")}
                </Button>
                <Button size="sm" variant="outline"
                        disabled={page * 20 >= total}
                        onClick={() => setPage(p => p + 1)}>
                  {t("common.next")}
                </Button>
              </div>
            </div>
          </>
        )}

        {/* ── Tab : Analytics ────────────────────────────────────────────── */}
        {activeTab === "analytics" && (
          <div className="space-y-6">
            <div className="flex flex-wrap gap-3 items-center">
              <select
                value={analyticsRole}
                onChange={e => setAnalyticsRole(e.target.value)}
                className="text-sm border rounded-lg px-3 py-2 bg-background text-foreground"
              >
                <option value="">{t("analytics.filters.all_visitors")}</option>
                <option value="anonymous">{t("analytics.filters.anonymous")}</option>
                <option value="user">{t("analytics.filters.users")}</option>
                <option value="premium">{t("analytics.filters.premium")}</option>
                <option value="admin">{t("analytics.filters.admins")}</option>
              </select>

              <div className="flex gap-2">
                {[7, 30, 90].map(d => (
                  <button
                    key={d}
                    onClick={() => setAnalyticsDays(d)}
                    className={`text-xs px-3 py-1.5 rounded-full border transition
                      ${analyticsDays === d
                        ? "border-indigo-500 text-indigo-400 bg-indigo-500/10"
                        : "border-white/10 text-muted-foreground hover:text-foreground"
                      }`}
                  >
                    {t("analytics.filters.days", { count: d })}
                  </button>
                ))}
              </div>

              <button
                onClick={fetchAnalytics}
                className="text-xs px-3 py-1.5 rounded-full border border-white/10
                           text-muted-foreground hover:text-foreground transition ml-auto"
              >
                {t("analytics.filters.refresh")}
              </button>

              <span className="text-sm text-muted-foreground">
                {t("analytics.total_visits", {
                  count: analyticsTotal,
                  count_plural: t("analytics.total_visits_plural"),
                })}
              </span>
            </div>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">{t("analytics.map_title")}</CardTitle>
              </CardHeader>
              <CardContent>
                <WorldMap countries={worldCountries} cities={worldCities} />
              </CardContent>
            </Card>

            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("analytics.timeline_title")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <VisitsTimeline data={timeline} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">{t("analytics.top_countries_title")}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {topCountries.map((c, i) => (
                      <div key={c.country_code} className="flex items-center gap-3">
                        <span className="text-xs text-muted-foreground w-4">{i + 1}</span>
                        <span className="text-sm flex-1">{c.country_name}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-20 bg-white/10 rounded-full h-1.5">
                            <div className="bg-indigo-500 h-1.5 rounded-full"
                                 style={{ width: `${c.pct}%` }} />
                          </div>
                          <span className="text-xs text-muted-foreground w-16 text-right">
                            {c.visits} ({c.pct}%)
                          </span>
                        </div>
                      </div>
                    ))}
                    {topCountries.length === 0 && (
                      <p className="text-sm text-muted-foreground text-center py-4">
                        {t("analytics.no_data")}
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        )}

        {/* ── Tab : Contenu ──────────────────────────────────────────────── */}
        {activeTab === "content" && (
          <div className="space-y-6">

            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold">{t("content.tutorials.title")}</h2>
              <div className="flex gap-2">
                {/* Import ZIP */}
                <Button variant="outline"
                        onClick={() => importInputRef.current?.click()}
                        disabled={importing}>
                  {importing ? "Import..." : "📦 Importer ZIP"}
                </Button>
                <input ref={importInputRef} type="file" accept=".zip"
                       onChange={handleImportTutorial} className="hidden" />
                <Button onClick={() => setShowTutorialForm(v => !v)}>
                  {t("content.tutorials.create_btn")}
                </Button>
              </div>
            </div>

            {/* Message import */}
            {importMsg && (
              <div className={`px-4 py-3 rounded-lg text-sm border ${
                importMsg.startsWith("✓")
                  ? "bg-green-500/10 border-green-500/20 text-green-400"
                  : "bg-red-500/10 border-red-500/20 text-red-400"
              }`}>
                {importMsg}
              </div>
            )}

            {/* Formulaire création */}
            {showTutorialForm && (
              <Card>
                <CardContent className="pt-6 space-y-4">
                  <input
                    placeholder={t("content.tutorials.form.title_placeholder")}
                    value={tTitle}
                    onChange={e => setTTitle(e.target.value)}
                    className="w-full bg-white/5 border border-white/10 rounded-lg
                               px-4 py-3 text-white placeholder-white/30 outline-none
                               focus:border-white/30"
                  />
                  <textarea
                    placeholder={t("content.tutorials.form.desc_placeholder")}
                    value={tDesc}
                    onChange={e => setTDesc(e.target.value)}
                    rows={3}
                    className="w-full bg-white/5 border border-white/10 rounded-lg
                               px-4 py-3 text-white placeholder-white/30 outline-none
                               focus:border-white/30 resize-none"
                  />
                  <div className="flex gap-4 items-center flex-wrap">
                    <select value={tRole} onChange={e => setTRole(e.target.value)}
                            className="text-sm border rounded-lg px-3 py-2 bg-background text-foreground">
                      <option value="user">{t("content.tutorials.form.access_free")}</option>
                      <option value="premium">{t("content.tutorials.form.access_premium")}</option>
                      <option value="admin">🔒 Interne (admin uniquement)</option>
                    </select>
                    <select value={tLang} onChange={e => setTLang(e.target.value)}
                            className="text-sm border rounded-lg px-3 py-2 bg-background text-foreground">
                      <option value="fr">🇫🇷 Français</option>
                      <option value="en">🇬🇧 English</option>
                    </select>
                    <label className="flex items-center gap-2 text-sm cursor-pointer">
                      <input type="checkbox" checked={tPublished}
                             onChange={e => setTPublished(e.target.checked)} />
                      {t("content.tutorials.form.publish_now")}
                    </label>
                  </div>
                  <div className="flex gap-3">
                    <Button onClick={createTutorial} disabled={!tTitle.trim()}>
                      {t("content.tutorials.form.create_confirm")}
                    </Button>
                    <Button variant="outline" onClick={() => setShowTutorialForm(false)}>
                      {t("content.tutorials.form.cancel")}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Liste tutoriaux */}
            <Card>
              <CardContent className="p-0">
                <table className="w-full text-sm">
                  <thead className="border-b bg-muted/50">
                    <tr>
                      {["title", "cover", "lang", "access", "lessons", "status", "actions"].map(h => (
                        <th key={h} className="px-4 py-3 text-left font-medium text-muted-foreground">
                          {t(`content.tutorials.table.${h}`)}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tutorials.map(tut => (
                      <tr key={tut.id} className="border-b hover:bg-muted/30 transition">
                        <td className="px-4 py-3 font-medium">{tut.title}</td>
                        {/* Cover — cliquable pour modifier */}
                        <td className="px-4 py-3">
                          <label className="cursor-pointer group/cover block w-10 h-10">
                            {tut.cover_image ? (
                              <img src={tut.cover_image} alt=""
                                   className="w-10 h-10 object-cover rounded-lg
                                              border border-white/10
                                              group-hover/cover:opacity-70 transition" />
                            ) : (
                              <div className="w-10 h-10 rounded-lg bg-white/5
                                              border border-dashed border-white/20
                                              flex items-center justify-center
                                              text-white/20 text-xs
                                              group-hover/cover:border-white/40 transition">
                                +
                              </div>
                            )}
                            <input
                              type="file" accept="image/*" className="hidden"
                              onChange={async (e) => {
                                const file = e.target.files?.[0];
                                if (!file) return;
                                const form = new FormData();
                                form.append("file", file);
                                const res = await fetch(`${API}/api/admin/media/upload`, {
                                  method:  "POST",
                                  headers: { Authorization: `Bearer ${accessToken}` },
                                  body:    form,
                                });
                                if (res.ok) {
                                  const data = await res.json();
                                  await apiFetch(`/admin/content/tutorials/${tut.id}`, {
                                    method: "PUT",
                                    body:   JSON.stringify({ cover_image: `${API}${data.url}` }),
                                  });
                                  fetchTutorials();
                                  showMsg("Cover mise à jour ✓");
                                }
                              }}
                            />
                          </label>
                        </td>
                        <td className="px-4 py-3 text-xs uppercase text-muted-foreground">
                          {tut.lang === "fr" ? "🇫🇷 FR" : "🇬🇧 EN"}
                        </td>
                        <td className="px-4 py-3">
                          <select
                            value={tut.access_role}
                            onChange={e => updateAccessRole(tut.id, e.target.value)}
                            className={`text-xs px-2 py-1 rounded-full border bg-transparent cursor-pointer
                              ${tut.access_role === "premium"
                                ? "text-yellow-400 border-yellow-500/30"
                                : tut.access_role === "admin"
                                ? "text-red-400 border-red-500/30"
                                : "text-white/50 border-white/20"
                              }`}
                          >
                            <option value="user" className="bg-slate-900 text-white">Gratuit</option>
                            <option value="premium" className="bg-slate-900 text-white">Premium</option>
                            <option value="admin" className="bg-slate-900 text-white">🔒 Admin</option>
                          </select>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {tut.lessons.length}
                        </td>
                        <td className="px-4 py-3">
                          <Badge variant={tut.is_published ? "default" : "secondary"}>
                            {tut.is_published
                              ? t("content.tutorials.status.published")
                              : t("content.tutorials.status.draft")}
                          </Badge>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex gap-2 flex-wrap">
                            <Button size="sm" variant="outline"
                                    onClick={() => togglePublishTutorial(tut.id, tut.is_published)}>
                              {tut.is_published
                                ? t("content.tutorials.actions.unpublish")
                                : t("content.tutorials.actions.publish")}
                            </Button>
                            <Button size="sm" variant="outline"
                                    onClick={() => navigate(`/admin/content/${tut.id}`)}>
                              {t("content.tutorials.actions.edit")}
                            </Button>
                            <Button size="sm" variant="outline"
                                    onClick={() => exportTutorial(tut.id, tut.slug)}
                                    title="Exporter en ZIP">
                              ↓
                            </Button>
                            <Button size="sm" variant="destructive"
                                    onClick={() => deleteTutorial(tut.id)}>
                              ✕
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                    {tutorials.length === 0 && (
                      <tr>
                        <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                          {t("content.tutorials.empty")}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </div>
        )}

        {/* ── Tab : Base de données ───────────────────────────────────────── */}
        {activeTab === "database" && (
          <div className="space-y-6">

            {dbLoading ? (
              <p className="text-muted-foreground text-sm">
                Chargement des statistiques...
              </p>
            ) : dbStats ? (
              <>
                {/* État de la base */}
                <div className="grid md:grid-cols-2 gap-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">État de la base</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Taille totale</span>
                        <span className="font-mono">{dbStats.db_size}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Dernière migration</span>
                        <span className="font-mono text-xs">{dbStats.last_migration}</span>
                      </div>
                      {dbStats.settings.last_cleanup_at && (
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Dernier nettoyage</span>
                          <span>
                            {new Date(dbStats.settings.last_cleanup_at)
                              .toLocaleDateString(i18n.language)}
                          </span>
                        </div>
                      )}
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-base">Lignes par table</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {Object.entries(dbStats.counts).map(([table, count]) => (
                          <div key={table}
                               className="flex justify-between items-center text-sm">
                            <span className="text-muted-foreground font-mono">{table}</span>
                            <div className="flex items-center gap-3">
                              <span className="text-xs text-muted-foreground">
                                {dbStats.table_sizes[table] ?? ""}
                              </span>
                              <span className="font-semibold w-16 text-right">
                                {(count as number).toLocaleString()}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Paramètres de nettoyage */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Nettoyage automatique</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid md:grid-cols-2 gap-4">
                      {[
                        { label: "Tokens expirés",     value: tokensDays, setter: setTokensDays },
                        { label: "Données de visites", value: visitsDays, setter: setVisitsDays },
                        { label: "Logs d'activité",    value: logsDays,   setter: setLogsDays },
                      ].map(({ label, value, setter }) => (
                        <div key={label} className="flex items-center gap-3">
                          <label className="text-sm text-muted-foreground flex-1">{label}</label>
                          <div className="flex items-center gap-2">
                            <input
                              type="number" min="1" max="3650"
                              value={value}
                              onChange={e => setter(parseInt(e.target.value) || 1)}
                              className="w-20 text-sm border rounded-lg px-2 py-1.5
                                         bg-background text-foreground text-center"
                            />
                            <span className="text-xs text-muted-foreground">jours</span>
                          </div>
                        </div>
                      ))}

                      <div className="flex items-center gap-3">
                        <label className="text-sm text-muted-foreground flex-1">
                          Fréquence automatique
                        </label>
                        <select value={frequency} onChange={e => setFrequency(e.target.value)}
                                className="text-sm border rounded-lg px-2 py-1.5
                                           bg-background text-foreground">
                          <option value="daily">Quotidien (3h)</option>
                          <option value="weekly">Hebdomadaire (lundi)</option>
                          <option value="monthly">Mensuel (1er du mois)</option>
                          <option value="disabled">Désactivé</option>
                        </select>
                      </div>
                    </div>

                    <div className="flex gap-3 pt-2 flex-wrap">
                      <Button onClick={saveDbSettings}>
                        Sauvegarder les paramètres
                      </Button>
                      <Button variant="outline" onClick={runCleanup}
                              disabled={cleanupRunning}>
                        {cleanupRunning ? "Nettoyage..." : "🧹 Nettoyer maintenant"}
                      </Button>
                      <Button variant="outline" onClick={runVacuum}
                              disabled={vacuumRunning}>
                        {vacuumRunning ? "VACUUM..." : "⚡ VACUUM ANALYZE"}
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Export / Import */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Export / Import</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid md:grid-cols-2 gap-6">

                      {/* Utilisateurs */}
                      <div className="space-y-3">
                        <h3 className="text-sm font-medium">Utilisateurs</h3>
                        <Button variant="outline" className="w-full"
                                onClick={exportUsers}>
                          ↓ Exporter utilisateurs (ZIP)
                        </Button>
                        <Button variant="outline" className="w-full"
                                onClick={() => importUsersRef.current?.click()}>
                          ↑ Importer utilisateurs (ZIP)
                        </Button>
                        <input ref={importUsersRef} type="file" accept=".zip"
                               onChange={handleImportUsers} className="hidden" />
                        {importUsersResult && (
                          <p className={`text-xs ${
                            importUsersResult.startsWith("✓")
                              ? "text-green-500" : "text-red-500"
                          }`}>
                            {importUsersResult}
                          </p>
                        )}
                      </div>

                      {/* Tutoriaux */}
                      <div className="space-y-3">
                        <h3 className="text-sm font-medium">Tutoriaux</h3>
                        <Button variant="outline" className="w-full"
                                onClick={exportTutorialsBulk}>
                          ↓ Exporter tous les tutoriaux (ZIP)
                        </Button>
                        <p className="text-xs text-muted-foreground">
                          Pour exporter un tutorial spécifique, utiliser
                          le bouton ↓ dans l'onglet Contenu.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Button onClick={fetchDbStats}>Charger les statistiques</Button>
            )}
          </div>
        )}

        {/* ── Onglet Sécurité ─────────────────────────────────────────────── */}
        {activeTab === "security" && (
          <div className="space-y-6">
            {/* Filtres */}
            <div className="flex gap-3 items-center flex-wrap">
              {[1, 7, 14, 30].map(d => (
                <button key={d}
                  onClick={() => { setSecDays(d); fetchSecurity(); }}
                  className={`text-xs px-3 py-1.5 rounded-lg border transition
                    ${secDays === d
                      ? "border-foreground bg-foreground text-background"
                      : "border-border text-muted-foreground hover:text-foreground"}`}>
                  {d === 1 ? "24h" : `${d}j`}
                </button>
              ))}
              <button onClick={fetchSecurity}
                className="text-xs px-3 py-1.5 rounded-lg border border-border
                           text-muted-foreground hover:text-foreground transition ml-auto">
                Actualiser
              </button>
            </div>

            {secLoading ? (
              <p className="text-muted-foreground text-sm">Chargement…</p>
            ) : (
              <>
                {/* Résumé */}
                {secSummary && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                      { label: "Total",      value: secSummary.total,   color: "" },
                      { label: "24 dernières heures", value: secSummary.last_24h, color: "text-yellow-500" },
                      { label: "Critiques",  value: secSummary.by_severity?.critical ?? 0, color: "text-red-500" },
                      { label: "Élevés",     value: secSummary.by_severity?.high ?? 0,     color: "text-orange-500" },
                    ].map(s => (
                      <Card key={s.label}>
                        <CardContent className="pt-5">
                          <p className={`text-2xl font-bold ${s.color}`}>{s.value}</p>
                          <p className="text-xs text-muted-foreground mt-1">{s.label}</p>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}

                {/* Top IPs */}
                {secSummary && secSummary.top_ips.length > 0 && (
                  <Card>
                    <CardHeader><CardTitle className="text-base">Top IPs agressives</CardTitle></CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {secSummary.top_ips.map(({ ip, hits }) => (
                          <div key={ip} className="flex justify-between text-sm">
                            <span className="font-mono text-xs">{ip}</span>
                            <Badge variant="destructive">{hits} requêtes</Badge>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Liste des événements */}
                <Card>
                  <CardHeader><CardTitle className="text-base">
                    Événements ({secEvents.length})
                  </CardTitle></CardHeader>
                  <CardContent>
                    {secEvents.length === 0 ? (
                      <p className="text-muted-foreground text-sm">Aucun événement sur cette période.</p>
                    ) : (
                      <div className="space-y-2 max-h-[600px] overflow-y-auto">
                        {secEvents.map(e => (
                          <div key={e.id}
                            className="flex flex-col gap-0.5 border-b pb-2 last:border-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <Badge variant={
                                e.severity === "critical" ? "destructive" :
                                e.severity === "high"     ? "destructive" : "secondary"
                              } className={
                                e.severity === "high"   ? "bg-orange-500/20 text-orange-400 border-orange-500/30" :
                                e.severity === "medium" ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30" : ""
                              }>
                                {e.severity}
                              </Badge>
                              <span className="text-xs text-muted-foreground font-mono">{e.event_type}</span>
                              <span className="text-xs font-mono ml-auto text-muted-foreground">
                                {new Date(e.created_at).toLocaleString(i18n.language)}
                              </span>
                            </div>
                            <div className="flex gap-3 text-xs text-muted-foreground flex-wrap">
                              <span className="font-mono">{e.ip_address}</span>
                              <span className="font-mono">{e.method} {e.path}</span>
                            </div>
                            {e.user_agent && (
                              <p className="text-xs text-muted-foreground/60 truncate">{e.user_agent}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        )}

      </div>
    </>
  );
}