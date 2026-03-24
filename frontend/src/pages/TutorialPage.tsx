import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import SEO from "../components/SEO";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function getImgUrl(path: string | null): string | null {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  return `${API}${path}`;
}

interface Lesson {
  id: number; title: string; slug: string;
  order: number; duration_minutes: number | null; is_published: boolean;
}
interface Tutorial {
  id: number; title: string; slug: string;
  description: string | null; cover_image: string | null;
  access_role: string; lessons: Lesson[];
}

export default function TutorialPage() {
  const { slug }            = useParams<{ slug: string }>();
  const [tutorial, setTutorial] = useState<Tutorial | null>(null);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState("");
  const { user }                = useAuth();
  const navigate                = useNavigate();

  useEffect(() => {
    fetch(`${API}/api/content/tutorials/${slug}`)
      .then(r => {
        if (!r.ok) throw new Error(String(r.status));
        return r.json();
      })
      .then(setTutorial)
      .catch(e => setError(e.message === "403"
        ? "Contenu réservé aux membres Premium"
        : "Tutorial introuvable"))
      .finally(() => setLoading(false));
  }, [slug]);

  const jsonLd = tutorial ? {
    "@context":    "https://schema.org",
    "@type":       "Course",
    "name":        tutorial.title,
    "description": tutorial.description ?? "",
    "url":         `${import.meta.env.VITE_SITE_URL}/learn/${tutorial.slug}`,
    "provider": {
      "@type": "Organization",
      "name":  import.meta.env.VITE_SITE_NAME ?? "0-HITL",
      "url":   import.meta.env.VITE_SITE_URL ?? "https://0-hitl.com",
    },
    "hasCourseInstance": tutorial.lessons
      .filter(l => l.is_published)
      .map((l, i) => ({
        "@type":      "CourseInstance",
        "name":       l.title,
        "courseMode": "online",
        "position":   i + 1,
      })),
  } : undefined;

  if (loading) return (
    <div className="min-h-screen bg-black text-white flex items-center
                    justify-center">
      <p className="text-white/30">Chargement...</p>
    </div>
  );

  if (error || !tutorial) return (
    <div className="min-h-screen bg-black text-white flex items-center
                    justify-center text-center px-4">
      <div>
        <p className="text-4xl mb-4">🔒</p>
        <h1 className="text-xl font-bold mb-4">{error || "Introuvable"}</h1>
        {error.includes("Premium") && !user && (
          <button onClick={() => navigate("/login")}
                  className="text-indigo-400 hover:text-indigo-300 underline">
            Se connecter
          </button>
        )}
        <button onClick={() => navigate("/learn")}
                className="mt-4 block text-white/40 hover:text-white transition">
          ← Retour au catalogue
        </button>
      </div>
    </div>
  );

  const publishedLessons = tutorial.lessons.filter(l => l.is_published);

  return (
    <>
      <SEO
        title={tutorial.title}
        description={tutorial.description ?? ""}
        image={getImgUrl(tutorial.cover_image) || undefined}
        url={`/learn/${tutorial.slug}`}
        type="article"
        jsonLd={jsonLd}
      />
      <div className="min-h-screen bg-black text-white">
        <div className="max-w-3xl mx-auto px-6 py-16">

          {/* Retour */}
          <button onClick={() => navigate("/learn")}
                  className="text-white/40 hover:text-white transition text-sm mb-8
                             flex items-center gap-2">
            ← Catalogue
          </button>

          {/* Cover */}
          {tutorial.cover_image && (
            <img src={getImgUrl(tutorial.cover_image) || ""} alt={tutorial.title}
                 className="w-full h-64 object-cover rounded-2xl mb-8
                            border border-white/10" />
          )}

          {/* Header */}
          <div className="mb-10">
            {tutorial.access_role === "premium" && (
              <span className="inline-flex text-xs px-2 py-0.5 rounded-full
                               bg-yellow-500/20 text-yellow-400
                               border border-yellow-500/30 mb-4">
                ⭐ Premium
              </span>
            )}
            <h1 className="text-4xl font-bold mb-4">{tutorial.title}</h1>
            {tutorial.description && (
              <p className="text-white/50 text-lg">{tutorial.description}</p>
            )}
            <p className="text-white/30 text-sm mt-3">
              {publishedLessons.length} leçon{publishedLessons.length > 1 ? "s" : ""}
            </p>
          </div>

          {/* Liste des leçons */}
          <div className="space-y-3">
            {publishedLessons.map((lesson, i) => (
              <button
                key={lesson.id}
                onClick={() => navigate(`/learn/${slug}/${lesson.slug}`)}
                className="w-full text-left flex items-center gap-4
                           border border-white/10 rounded-xl px-5 py-4
                           hover:border-white/30 hover:bg-white/5 transition group"
              >
                <span className="w-8 h-8 rounded-full bg-white/10 flex items-center
                                 justify-center text-sm font-mono text-white/50
                                 group-hover:bg-white/20 transition flex-shrink-0">
                  {i + 1}
                </span>
                <span className="flex-1 font-medium group-hover:text-white
                                 transition">
                  {lesson.title}
                </span>
                {lesson.duration_minutes && (
                  <span className="text-xs text-white/30">
                    {lesson.duration_minutes} min
                  </span>
                )}
                <span className="text-white/20 group-hover:text-white/60
                                 transition">
                  →
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
