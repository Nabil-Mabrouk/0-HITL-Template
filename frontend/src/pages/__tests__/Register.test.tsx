import { describe, it, expect, vi } from "vitest";
import { render } from "../../test/utils";
import Register from "../Register";

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useSearchParams: () => [new URLSearchParams(), vi.fn()],
  };
});

vi.mock("../../context/AuthContext", () => ({
  useAuth: () => ({
    login: vi.fn(),
    user: null,
    isLoading: false,
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

describe("Register page", () => {
  it("rend sans erreur", () => {
    expect(() => render(<Register />)).not.toThrow();
  });
});
