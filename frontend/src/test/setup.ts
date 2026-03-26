import "@testing-library/jest-dom";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

// Nettoie le DOM après chaque test
afterEach(() => {
  cleanup();
});

// Mock de localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

Object.defineProperty(window, "localStorage", { value: localStorageMock });

// Mock de fetch (remplacé par MSW dans les tests qui en ont besoin)
global.fetch = vi.fn();

// Mock de import.meta.env
vi.stubEnv("VITE_API_URL", "http://localhost:8000");
