import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import MarkdownRenderer from "@/components/MarkdownRenderer";
import { useTranslation } from "react-i18next";
import SEO from "@/components/SEO";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// ── Types ──────────────────────────────────────────────────────────────────

interface Lesson {
  id: number; title: string; slug: string; order: number;
  content: string | null; duration_minutes: number | null;
  is_published: boolean;
}
interface Tutorial {
  id: number; title: string; slug: string;
  access_role: string; is_published: boolean;
}
interface MediaFile {
  filename: string;
  url:      string;
  type:     "image" | "video" | "audio" | "document" | "other";
  size:     number;
  original?: string;
}

// ── Helpers ────────────────────────────────────────────────────────────────

function formatSize(bytes: number): string {
  if (bytes < 1024)        return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getMarkdownSnippet(file: MediaFile): string {
  const url = `${API}${file.url}`;
  switch (file.type) {
    case "image":    return `![${file.filename}](${url})`;
    case "video":    return `[video:${url}]`;
    case "audio":    return `[audio:${url}]`;
    case "document": return `[📄 ${file.filename}](${url})`;
    default:         return `[${file.filename}](${url})`;
  }
}

// ── Composant principal ────────────────────────────────────────────────────

export default function ContentEditor() {
  const { tutorialId }  = useParams<{ tutorialId: string }>();
  const { accessToken } = useAuth();
  const navigate        = useNavigate();
  const { t }           = useTranslation("admin");

  // ── Tutorial & leçons
  const [tutorial, setTutorial]     = useState<Tutorial | null>(null);
  const [lessons, setLessons]       = useState<Lesson[]>([]);
  const [selected, setSelected]     = useState<Lesson | null>(null);

  // ── Éditeur
  const [preview, setPreview]       = useState(false);
  const [saving, setSaving]         = useState(false);
  const [msg, setMsg]               = useState("");
  const [lTitle, setLTitle]         = useState("");
  const [lContent, setLContent]     = useState("");
  const [lMins, setLMins]           = useState("");
  const [lPublished, setLPublished] = useState(false);
  const textareaRef                 = useRef<HTMLTextAreaElement>(null);

  // ── Nouvelle leçon
  const [showNewLesson, setShowNewLesson] = useState(false);
  const [newLessonTitle, setNewLessonTitle] = useState("");

  // ── Médias
  const [mediaFiles, setMediaFiles]     = useState<MediaFile[]>([]);
  const [mediaLoading, setMediaLoading] = useState(false);
  const [uploading, setUploading]       = useState(false);
  const [showMedia, setShowMedia]       = useState(true);
  const [mediaFilter, setMediaFilter]   = useState<string>("all");
  const fileInputRef                    = useRef<HTMLInputElement>(null);

  const headers = {
    "Content-Type": "application/json",
    Authorization:  `Bearer ${accessToken}`,
  };

  // ── Init ──────────────────────────────────────────────────────────────────
  useEffect(() => {
    loadTutorial();
    loadMedia();
  }, [tutorialId]);

  async function loadTutorial() {
    const [tutRes, lessonsRes] = await Promise.all([
      fetch(`${API}/api/admin/content/tutorials?per_page=100`, { headers }),
      fetch(`${API}/api/admin/content/tutorials/${tutorialId}/lessons`,
            { headers }),
    ]);
    if (tutRes.ok) {
      const data = await tutRes.json();
      const tData = data.tutorials?.find(
        (tut: Tutorial) => String(tut.id) === tutorialId
      );
      setTutorial(tData ?? null);
    }
    if (lessonsRes.ok) setLessons(await lessonsRes.json());
  }

  async function loadMedia() {
    setMediaLoading(true);
    const res = await fetch(`${API}/api/admin/media/list`, { headers });
    if (res.ok) setMediaFiles((await res.json()).files);
    setMediaLoading(false);
  }

  // ── Sélection leçon ───────────────────────────────────────────────────────
  function selectLesson(l: Lesson) {
    setSelected(l);
    setLTitle(l.title);
    setLContent(l.content ?? "");
    setLMins(String(l.duration_minutes ?? ""));
    setLPublished(l.is_published);
    setPreview(false);
  }

  // ── Sauvegarde ────────────────────────────────────────────────────────────
  async function saveLesson() {
    if (!selected) return;
    setSaving(true);
    const res = await fetch(
      `${API}/api/admin/content/tutorials/${tutorialId}/lessons/${selected.id}`,
      {
        method: "PUT", headers,
        body: JSON.stringify({
          title:            lTitle,
          content:          lContent,
          duration_minutes: lMins ? parseInt(lMins) : null,
          is_published:     lPublished,
        }),
      }
    );
    if (res.ok) {
      const updated = await res.json();
      setMsg(t("content.editor.saved"));
      setTimeout(() => setMsg(""), 2000);
      setLessons(ls => ls.map(l => l.id === updated.id ? updated : l));
      setSelected(updated);
    }
    setSaving(false);
  }

  // ── Nouvelle leçon ────────────────────────────────────────────────────────
  async function createLesson() {
    if (!newLessonTitle.trim()) return;
    const res = await fetch(
      `${API}/api/admin/content/tutorials/${tutorialId}/lessons`,
      {
        method: "POST", headers,
        body: JSON.stringify({
          title:   newLessonTitle,
          order:   lessons.length,
          content: "",
        }),
      }
    );
    if (res.ok) {
      const l = await res.json();
      setLessons(ls => [...ls, l]);
      selectLesson(l);
      setShowNewLesson(false);
      setNewLessonTitle("");
    }
  }

  // ── Upload média ──────────────────────────────────────────────────────────
  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    for (const file of Array.from(files)) {
      const form = new FormData();
      form.append("file", file);
      await fetch(`${API}/api/admin/media/upload`, {
        method:  "POST",
        headers: { Authorization: `Bearer ${accessToken}` },
        body:    form,
      });
    }
    await loadMedia();
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  // ── Supprimer média ───────────────────────────────────────────────────────
  async function deleteMedia(filename: string) {
    if (!confirm(t("content.editor.media.item.delete_confirm", { filename }))) return;
    await fetch(`${API}/api/admin/media/${filename}`, {
      method: "DELETE", headers,
    });
    setMediaFiles(fs => fs.filter(f => f.filename !== filename));
  }

  // ── Insérer snippet dans le textarea ─────────────────────────────────────
  function insertSnippet(file: MediaFile) {
    const snippet = getMarkdownSnippet(file);
    const ta      = textareaRef.current;
    if (!ta) {
      setLContent(c => c + "\n" + snippet);
      return;
    }
    const start  = ta.selectionStart;
    const end    = ta.selectionEnd;
    const before = lContent.slice(0, start);
    const after  = lContent.slice(end);
    const newContent = `${before}\n${snippet}\n${after}`;
    setLContent(newContent);
    // Repositionner le curseur
    setTimeout(() => {
      ta.focus();
      ta.setSelectionRange(start + snippet.length + 2,
                           start + snippet.length + 2);
    }, 0);
  }

  // ── Médias filtrés ────────────────────────────────────────────────────────
  const filteredMedia = mediaFilter === "all"
    ? mediaFiles
    : mediaFiles.filter(f => f.type === mediaFilter);

  const typeIcon: Record<string, string> = {
    image: "🖼️", video: "🎬", audio: "🎵", document: "📄", other: "📎",
  };

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <>
      <SEO title={t("content.tutorials.title")} noindex={true} />
      <div className="min-h-screen bg-black text-white flex">

        {/* ── Sidebar gauche : leçons ───────────────────────────────────── */}
        <aside className="w-64 border-r border-white/10 flex flex-col flex-shrink-0">
          <div className="p-4 border-b border-white/10">
            <button
              onClick={() => navigate("/admin")}
              className="text-white/40 hover:text-white text-sm transition mb-3 block"
            >
              {t("content.editor.back")}
            </button>
            <h2 className="font-semibold truncate text-sm">
              {tutorial?.title ?? t("content.editor.loading")}
            </h2>
            <p className="text-white/30 text-xs mt-1">
              {t("content.editor.lessons_sidebar.count", { count: lessons.length, count_plural: t("content.editor.lessons_sidebar.count_plural") })}
            </p>
          </div>

          <div className="flex-1 overflow-y-auto p-3 space-y-1">
            {lessons.sort((a, b) => a.order - b.order).map((l, i) => (
              <button
                key={l.id}
                onClick={() => selectLesson(l)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-sm
                            transition flex items-center gap-2
                            ${selected?.id === l.id
                              ? "bg-white/10 text-white"
                              : "text-white/50 hover:bg-white/5 hover:text-white"
                            }`}
              >
                <span className="text-xs text-white/30 w-5 flex-shrink-0">
                  {i + 1}
                </span>
                <span className="flex-1 truncate">{l.title}</span>
                {!l.is_published && (
                  <span className="w-1.5 h-1.5 rounded-full bg-yellow-500
                                   flex-shrink-0" title={t("content.editor.lessons_sidebar.draft_badge")} />
                )}
              </button>
            ))}
          </div>

          <div className="p-3 border-t border-white/10">
            {showNewLesson ? (
              <div className="space-y-2">
                <input
                  placeholder={t("content.editor.lessons_sidebar.new_placeholder")}
                  value={newLessonTitle}
                  onChange={e => setNewLessonTitle(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && createLesson()}
                  autoFocus
                  className="w-full bg-white/5 border border-white/10 rounded-lg
                             px-3 py-2 text-sm text-white placeholder-white/30
                             outline-none focus:border-white/30"
                />
                <div className="flex gap-2">
                  <button
                    onClick={createLesson}
                    disabled={!newLessonTitle.trim()}
                    className="flex-1 bg-white text-black text-xs font-semibold
                               py-2 rounded-lg disabled:opacity-50"
                  >
                    {t("content.editor.lessons_sidebar.new_confirm")}
                  </button>
                  <button
                    onClick={() => { setShowNewLesson(false); setNewLessonTitle(""); }}
                    className="text-white/40 text-xs px-2 hover:text-white transition"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowNewLesson(true)}
                className="w-full text-sm text-white/40 hover:text-white transition
                           py-2 border border-white/10 rounded-lg hover:border-white/30"
              >
                {t("content.editor.lessons_sidebar.new_btn")}
              </button>
            )}
          </div>
        </aside>

        {/* ── Zone centrale : éditeur ───────────────────────────────────── */}
        {selected ? (
          <main className="flex-1 flex flex-col min-w-0">

            {/* Toolbar */}
            <div className="border-b border-white/10 px-5 py-3 flex items-center
                            gap-3 flex-wrap">
              <input
                value={lTitle}
                onChange={e => setLTitle(e.target.value)}
                className="flex-1 min-w-0 bg-transparent text-base font-semibold
                           outline-none placeholder-white/30"
                placeholder={t("content.editor.lesson_form.title_placeholder")}
              />
              <input
                type="number" min="1" placeholder={t("content.editor.lesson_form.mins_placeholder")}
                value={lMins} onChange={e => setLMins(e.target.value)}
                title={t("content.editor.lesson_form.mins_title")}
                className="w-20 bg-white/5 border border-white/10 rounded-lg
                           px-2 py-1.5 text-sm text-white placeholder-white/30
                           outline-none text-center"
              />
              <label className="flex items-center gap-1.5 text-sm cursor-pointer
                                text-white/60 hover:text-white transition">
                <input
                  type="checkbox" checked={lPublished}
                  onChange={e => setLPublished(e.target.checked)}
                />
                {t("content.editor.lesson_form.published")}
              </label>
              <button
                onClick={() => setPreview(v => !v)}
                className={`text-sm px-3 py-1.5 rounded-lg border transition
                  ${preview
                    ? "border-indigo-500 text-indigo-400 bg-indigo-500/10"
                    : "border-white/10 text-white/40 hover:text-white"
                  }`}
              >
                {preview ? t("content.editor.edit_btn") : t("content.editor.preview_btn")}
              </button>
              <button
                onClick={() => setShowMedia(v => !v)}
                className={`text-sm px-3 py-1.5 rounded-lg border transition
                  ${showMedia
                    ? "border-white/30 text-white"
                    : "border-white/10 text-white/40 hover:text-white"
                  }`}
                title={t("content.editor.media_btn")}
              >
                {t("content.editor.media_btn")}
              </button>
              {msg && <span className="text-green-400 text-sm">{msg}</span>}
              <button
                onClick={saveLesson} disabled={saving}
                className="bg-white text-black text-sm font-semibold px-4 py-1.5
                           rounded-lg hover:bg-white/90 transition disabled:opacity-50"
              >
                {saving ? t("content.editor.saving") : t("content.editor.save_btn")}
              </button>
            </div>

            {/* Corps éditeur / aperçu */}
            <div className="flex-1 overflow-hidden flex">
              {preview ? (
                <div className="flex-1 overflow-y-auto">
                  <div className="max-w-3xl mx-auto px-8 py-8">
                    <MarkdownRenderer content={lContent} />
                  </div>
                </div>
              ) : (
                <textarea
                  ref={textareaRef}
                  value={lContent}
                  onChange={e => setLContent(e.target.value)}
                  placeholder={t("content.editor.lesson_form.content_placeholder")}
                  className="flex-1 bg-transparent text-white/80 font-mono text-sm
                             leading-relaxed px-8 py-8 outline-none resize-none
                             placeholder-white/20"
                />
              )}
            </div>
          </main>
        ) : (
          <main className="flex-1 flex items-center justify-center">
            <p className="text-white/20 text-sm">
              {t("content.editor.no_selection")}
            </p>
          </main>
        )}

        {/* ── Sidebar droite : médias ───────────────────────────────────── */}
        {showMedia && (
          <aside className="w-72 border-l border-white/10 flex flex-col
                            flex-shrink-0">

            {/* Header médias */}
            <div className="p-4 border-b border-white/10">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold">{t("content.editor.media.title")}</h3>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                  className="text-xs bg-white text-black font-semibold px-3 py-1.5
                             rounded-lg hover:bg-white/90 transition disabled:opacity-50"
                >
                  {uploading ? t("content.editor.media.uploading") : t("content.editor.media.upload_btn")}
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept="image/*,video/mp4,video/webm,audio/mpeg,audio/mp3,application/pdf"
                  onChange={handleUpload}
                  className="hidden"
                />
              </div>

              {/* Filtres type */}
              <div className="flex gap-1 flex-wrap">
                {["all", "image", "video", "audio", "document"].map(mType => (
                  <button
                    key={mType}
                    onClick={() => setMediaFilter(mType)}
                    className={`text-xs px-2 py-1 rounded-full border transition
                      ${mediaFilter === mType
                        ? "border-white/40 text-white bg-white/10"
                        : "border-white/10 text-white/30 hover:text-white"
                      }`}
                  >
                    {mType === "all" ? t("content.editor.media.filters.all") : typeIcon[mType]}
                  </button>
                ))}
              </div>
            </div>

            {/* Liste médias */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {mediaLoading ? (
                <p className="text-white/30 text-xs text-center py-4">
                  {t("common.loading")}
                </p>
              ) : filteredMedia.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-3xl mb-2">📁</p>
                  <p className="text-white/30 text-xs">
                    {mediaFilter === "all"
                      ? t("content.editor.media.empty")
                      : t("content.editor.media.empty_type")}
                  </p>
                </div>
              ) : (
                filteredMedia.map(file => (
                  <div
                    key={file.filename}
                    className="group border border-white/10 rounded-xl overflow-hidden
                               hover:border-white/30 transition"
                  >
                    {/* Aperçu image */}
                    {file.type === "image" && (
                      <img
                        src={`${API}${file.url}`}
                        alt={file.filename}
                        className="w-full h-28 object-cover"
                      />
                    )}

                    {/* Aperçu vidéo */}
                    {file.type === "video" && (
                      <video
                        src={`${API}${file.url}`}
                        className="w-full h-28 object-cover bg-black"
                        controls={false}
                      />
                    )}

                    {/* Icône pour audio/document */}
                    {(file.type === "audio" || file.type === "document") && (
                      <div className="h-16 flex items-center justify-center
                                      bg-white/5 text-3xl">
                        {typeIcon[file.type]}
                      </div>
                    )}

                    {/* Infos + actions */}
                    <div className="p-2">
                      <p className="text-xs text-white/60 truncate mb-1">
                        {file.filename}
                      </p>
                      <p className="text-xs text-white/30 mb-2">
                        {formatSize(file.size)}
                      </p>
                      <div className="flex gap-2">
                        {/* Insérer dans la leçon */}
                        <button
                          onClick={() => insertSnippet(file)}
                          disabled={!selected}
                          title={selected
                            ? t("content.editor.media.item.insert_tooltip")
                            : t("content.editor.media.item.insert_error")}
                          className="flex-1 text-xs py-1.5 bg-indigo-500/20
                                     text-indigo-400 border border-indigo-500/30
                                     rounded-lg hover:bg-indigo-500/30 transition
                                     disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                          {t("content.editor.media.item.insert_btn")}
                        </button>
                        {/* Copier l'URL */}
                        <button
                          onClick={() => navigator.clipboard.writeText(
                            `${API}${file.url}`
                          )}
                          title={t("content.editor.media.item.copy_tooltip")}
                          className="text-xs px-2 py-1.5 border border-white/10
                                     text-white/40 rounded-lg hover:text-white
                                     hover:border-white/30 transition"
                        >
                          📋
                        </button>
                        {/* Supprimer */}
                        <button
                          onClick={() => deleteMedia(file.filename)}
                          title={t("content.editor.media.item.delete_tooltip")}
                          className="text-xs px-2 py-1.5 border border-white/10
                                     text-red-400/50 rounded-lg
                                     hover:text-red-400 hover:border-red-400/30
                                     transition"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                  </div>
                )
              ))}
            </div>

            {/* Footer médias */}
            <div className="p-3 border-t border-white/10">
              <p className="text-xs text-white/20 text-center">
                {t("content.editor.media.footer", { count: mediaFiles.length, count_plural: t("content.editor.media.footer_plural") })}
                {" · "}{t("content.editor.media.drag_drop")}
              </p>
            </div>
          </aside>
        )}
      </div>
    </>
  );
}
