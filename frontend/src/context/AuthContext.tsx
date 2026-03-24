import { createContext, useContext, useState, useEffect } from "react";
import type { ReactNode } from "react";

interface User {
  id:          number;
  email:       string;
  full_name:   string | null;
  role:        string;
  is_verified: boolean;
}

interface AuthContextType {
  user:        User | null;
  accessToken: string | null;
  login:       (access: string) => void;
  logout:      () => Promise<void>;
  isAdmin:     boolean;
  isPremium:   boolean;
  isLoading:   boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);
const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser]               = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(
    localStorage.getItem("access_token")
  );
  const [isLoading, setIsLoading]     = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) fetchProfile(token);
    else setIsLoading(false);
  }, []);

  async function fetchProfile(token: string) {
    try {
      const res = await fetch(`${API}/api/users/me`, {
        headers: { Authorization: `Bearer ${token}` },
        credentials: "include",   // envoie les cookies avec la requête
      });
      if (res.ok) setUser(await res.json());
      else {
        localStorage.removeItem("access_token");
        setAccessToken(null);
      }
    } finally {
      setIsLoading(false);
    }
  }

  async function login(access: string): Promise<void> {
    localStorage.setItem("access_token", access);
    setAccessToken(access);
    await fetchProfile(access);    // <- await
  }

  async function logout() {
    try {
      // Appel backend pour révoquer le refresh token et supprimer le cookie
      await fetch(`${API}/api/auth/logout`, {
        method:      "POST",
        credentials: "include",
        headers: {
          Authorization:  `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
      });
    } catch (_) {
      // On continue même si l'appel API échoue (ex: déconnecté d'internet)
    }
    localStorage.removeItem("access_token");
    setAccessToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{
      user, accessToken, login, logout, isLoading,
      isAdmin:   user?.role === "admin",
      isPremium: ["premium", "admin"].includes(user?.role ?? ""),
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};