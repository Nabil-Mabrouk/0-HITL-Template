import "./i18n";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import { AuthProvider } from "./context/AuthContext";
import { usePageTracking } from "./hooks/usePageTracking";
import Navbar from "./components/Navbar";
import App from "./App";
import "./index.css";

document.documentElement.classList.add("dark");

function AppWithTracking() {
  usePageTracking();
  return (
    <>
      <Navbar />
      <div className="pt-14">
        <App />
      </div>
    </>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <HelmetProvider>
      <BrowserRouter>
        <AuthProvider>
          <AppWithTracking />
        </AuthProvider>
      </BrowserRouter>
    </HelmetProvider>
  </StrictMode>
);
