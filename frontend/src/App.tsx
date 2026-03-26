import { Routes, Route, Navigate, useSearchParams } from "react-router-dom";
import { useAuth } from "./context/AuthContext";

// Pages publiques
import Landing        from "./pages/Landing";
import Login          from "./pages/Login";
import Register       from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword  from "./pages/ResetPassword";
import VerifyEmail    from "./pages/VerifyEmail";

// Auth canaux
import AuthRouter     from "./auth/AuthRouter";
import RegisterDirect from "./pages/RegisterDirect";
import Onboarding     from "./pages/Onboarding";

// Pages protégées
import Profile        from "./pages/Profile";

// Admin
import AdminDashboard from "./pages/admin/Dashboard";
import ContentEditor  from "./pages/admin/ContentEditor";

// Contenu / Université virtuelle
import Learn          from "./pages/Learn";
import TutorialPage   from "./pages/TutorialPage";
import LessonPage     from "./pages/LessonPage";

// Monétisation
import Shop        from "./pages/Shop";
import ShopSuccess from "./pages/ShopSuccess";
import Premium     from "./pages/Premium";

// ── Guards ─────────────────────────────────────────────────────────────────

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return (
    <div className="min-h-screen flex items-center justify-center text-white">
      Chargement...
    </div>
  );
  return user ? <>{children}</> : <Navigate to="/login" replace />;
}

function GuestRoute({
  children,
  allowUpdate = false,
}: {
  children:     React.ReactNode;
  allowUpdate?: boolean;
}) {
  const { user, isLoading } = useAuth();
  const [searchParams]      = useSearchParams();

  if (isLoading) return (
    <div className="min-h-screen flex items-center justify-center text-white">
      Chargement...
    </div>
  );

  // Laisser passer si ?update=true et user connecté (mode re-onboarding)
  if (user && allowUpdate && searchParams.get("update") === "true") {
    return <>{children}</>;
  }

  return user ? <Navigate to="/profile" replace /> : <>{children}</>;
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const { user, isAdmin, isLoading } = useAuth();
  if (isLoading) return (
    <div className="min-h-screen flex items-center justify-center text-white">
      Chargement...
    </div>
  );
  if (!user)    return <Navigate to="/login" replace />;
  if (!isAdmin) return <Navigate to="/"      replace />;
  return <>{children}</>;
}

// ── App ────────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <Routes>

      {/* ── Public ─────────────────────────────────────────────────── */}
      <Route path="/" element={<Landing />} />

      <Route path="/login" element={
        <GuestRoute><Login /></GuestRoute>
      } />
      <Route path="/register" element={
        <GuestRoute><Register /></GuestRoute>
      } />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password"  element={<ResetPassword />} />
      <Route path="/verify-email"    element={<VerifyEmail />} />

      {/* ── Canaux d'auth ───────────────────────────────────────────── */}
      <Route path="/signup" element={<AuthRouter />} />
      <Route path="/register-direct" element={
        <GuestRoute><RegisterDirect /></GuestRoute>
      } />
      <Route path="/join" element={
        <GuestRoute allowUpdate={true}><Onboarding /></GuestRoute>
      } />

      {/* ── Contenu / Université virtuelle ──────────────────────────── */}
      <Route path="/learn"                   element={<Learn />} />
      <Route path="/learn/:slug"             element={<TutorialPage />} />
      <Route path="/learn/:slug/:lessonSlug" element={<LessonPage />} />

      {/* ── Monétisation ────────────────────────────────────────────── */}
      <Route path="/shop"         element={<Shop />} />
      <Route path="/shop/success" element={<ShopSuccess />} />
      <Route path="/premium"      element={<Premium />} />

      {/* ── Protégé ─────────────────────────────────────────────────── */}
      <Route path="/profile" element={
        <PrivateRoute><Profile /></PrivateRoute>
      } />

      {/* ── Admin ───────────────────────────────────────────────────── */}
      <Route path="/admin" element={
        <AdminRoute><AdminDashboard /></AdminRoute>
      } />
      <Route path="/admin/content/:tutorialId" element={
        <AdminRoute><ContentEditor /></AdminRoute>
      } />

      {/* ── Fallback ────────────────────────────────────────────────── */}
      <Route path="*" element={<Navigate to="/" replace />} />

    </Routes>
  );
}

