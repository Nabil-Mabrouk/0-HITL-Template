/**
 * Utilitaires de test partagés.
 *
 * Fournit un wrapper avec tous les providers nécessaires (Router, Auth, i18n)
 * et des helpers pour les rendus de composants.
 */

import React from "react";
import { render, RenderOptions } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

// Wrapper minimal avec Router pour les composants qui utilisent react-router
function AllProviders({ children }: { children: React.ReactNode }) {
  return (
    <MemoryRouter>
      {children}
    </MemoryRouter>
  );
}

/**
 * Render avec providers (Router, etc.)
 */
function renderWithProviders(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, "wrapper">
) {
  return render(ui, { wrapper: AllProviders, ...options });
}

export * from "@testing-library/react";
export { renderWithProviders as render };
