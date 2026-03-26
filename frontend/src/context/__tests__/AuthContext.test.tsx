import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import React from "react";
import { AuthProvider } from "../AuthContext";

// Hook helper pour accéder au contexte
async function renderAuthProvider() {
  const { result } = renderHook(
    () => {
      const { useContext } = React;
      // Import inline pour éviter les problèmes de circular deps en test
      const ctx = React.useContext(
        // @ts-ignore — accès direct au contexte exporté
        require("../AuthContext").AuthContext
      );
      return ctx;
    },
    {
      wrapper: ({ children }: { children: React.ReactNode }) => (
        <AuthProvider>{children}</AuthProvider>
      ),
    }
  );
  return result;
}

describe("AuthProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.resetAllMocks();
  });

  it("initialise sans utilisateur si pas de token", async () => {
    localStorage.removeItem("access_token");
    const mockFetch = vi.fn().mockResolvedValue({ ok: false });
    global.fetch = mockFetch;

    const result = await renderAuthProvider();

    await waitFor(() => {
      expect(result.current?.isLoading).toBe(false);
    });

    expect(result.current?.user).toBeNull();
  });

  it("appelle fetchProfile si un token existe en localStorage", async () => {
    localStorage.setItem("access_token", "fake-token");

    const mockUser = {
      id: 1,
      email: "test@test.com",
      full_name: "Test User",
      role: "user",
      is_verified: true,
    };
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockUser,
    });

    const result = await renderAuthProvider();

    await waitFor(() => {
      expect(result.current?.isLoading).toBe(false);
    });

    expect(result.current?.user?.email).toBe("test@test.com");
  });

  it("la fonction login stocke le token et met à jour l'état", async () => {
    global.fetch = vi.fn().mockResolvedValue({ ok: false });

    const result = await renderAuthProvider();

    await waitFor(() => expect(result.current?.isLoading).toBe(false));

    act(() => {
      result.current?.login("new-access-token");
    });

    expect(localStorage.getItem("access_token")).toBe("new-access-token");
  });
});
