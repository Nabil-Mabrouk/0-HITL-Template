import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import MarkdownRenderer from "../components/MarkdownRenderer";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface Lesson {
  id: number; title: string; order: number;
  content: string | null; duration_minutes: number | null;
  tutorial_id: number;
}
interface Tutorial {
  title: string; slug: string;
  lessons: { id: number; title: string; slug: string;
             order: number; is_published: boolean }[];
}

export default function LessonPage() {
  const { slug, lessonSlug } = useParams<{ slug: string; lessonSlug: string }>();
  const navigate              = useNavigate();

  const [lesson, setLesson]     = useState<Lesson | null>(null);
  const [tutorial, setTutorial] = useState<Tutorial | null>(null);
  const [loading, setLoading]   = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {};
    Promise.all([
      fetch(`${API}/api/content/tutorials/${slug}/${lessonSlug}`, { headers })
        .then(r => r.ok ? r.json() : null),
      fetch(`${API}/api/content/tutorials/${slug}`, { headers })
        .then(r => r.ok ? r.json() : null),
    ]).then(([lessonData, tutorialData]) => {
      setLesson(lessonData);
      setTutorial(tutorialData);
    }).finally(() => setLoading(false));
  }, [slug, lessonSlug]);

  if (loading) return (
    <div className="min-h-screen bg-black text-white flex items-center
                    justify-center">
      <p className="text-white/30">Chargement...</p>
    </div>
  );

  if (!lesson) return (
    <div className="min-h-screen bg-black text-white flex items-center
                    justify-center">
      <p className="text-white/40">Leçon introuvable</p>
    </div>
  );

  // Navigation prev/next
  const publishedLessons = tutorial?.lessons.filter(l => l.is_published)
    .sort((a, b) => a.order - b.order) ?? [];
  const currentIdx = publishedLessons.findIndex(l => l.slug === lessonSlug);
  const prevLesson = currentIdx > 0 ? publishedLessons[currentIdx - 1] : null;
  const nextLesson = currentIdx < publishedLessons.length - 1
    ? publishedLessons[currentIdx + 1] : null;

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="max-w-4xl mx-auto px-6 py-16">

        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm text-white/30 mb-8">
          <button onClick={() => navigate("/learn")}
                  className="hover:text-white transition">
            Catalogue
          </button>
          <span>/</span>
          <button onClick={() => navigate(`/learn/${slug}`)}
                  className="hover:text-white transition">
            {tutorial?.title}
          </button>
          <span>/</span>
          <span className="text-white/60">{lesson.title}</span>
        </div>

        {/* Header leçon */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-3">
            <span className="text-xs text-white/30 font-mono">
              Leçon {lesson.order + 1}
            </span>
            {lesson.duration_minutes && (
              <span className="text-xs text-white/30">
                · {lesson.duration_minutes} min
              </span>
            )}
          </div>
          <h1 className="text-3xl font-bold">{lesson.title}</h1>
        </div>

        {/* Contenu Markdown */}
        {lesson.content ? (
          <MarkdownRenderer content={lesson.content} />
        ) : (
          <p className="text-white/30 italic">Contenu à venir...</p>
        )}

        {/* Navigation prev/next */}
        <div className="flex items-center justify-between mt-16 pt-8
                        border-t border-white/10">
          {prevLesson ? (
            <button
              onClick={() => navigate(`/learn/${slug}/${prevLesson.slug}`)}
              className="flex items-center gap-2 text-sm text-white/40
                         hover:text-white transition group"
            >
              <span className="group-hover:-translate-x-1 transition">←</span>
              <div className="text-left">
                <p className="text-xs text-white/20">Précédent</p>
                <p>{prevLesson.title}</p>
              </div>
            </button>
          ) : <div />}

          {nextLesson ? (
            <button
              onClick={() => navigate(`/learn/${slug}/${nextLesson.slug}`)}
              className="flex items-center gap-2 text-sm text-white/40
                         hover:text-white transition group text-right"
            >
              <div>
                <p className="text-xs text-white/20">Suivant</p>
                <p>{nextLesson.title}</p>
              </div>
              <span className="group-hover:translate-x-1 transition">→</span>
            </button>
          ) : (
            <button
              onClick={() => navigate(`/learn/${slug}`)}
              className="text-sm text-indigo-400 hover:text-indigo-300 transition"
            >
              Terminer le tutorial ✓
            </button>
          )}
        </div>
      </div>
    </div>
  );
}