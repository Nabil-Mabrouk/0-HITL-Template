import "./i18n";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./lib/ThemeProvider";
import { usePageTracking } from "./hooks/usePageTracking";
import Navbar from "./components/Navbar";
import App from "./App";
import "./index.css";

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
        <ThemeProvider>
          <AuthProvider>
            <AppWithTracking />
          </AuthProvider>
        </ThemeProvider>
      </BrowserRouter>
    </HelmetProvider>
  </StrictMode>
);
