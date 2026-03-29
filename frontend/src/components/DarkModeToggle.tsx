/**
 * DarkModeToggle
 * ─────────────────────────────────────────────────────────────────────────────
 * A Sun/Moon button that flips dark ↔ light mode.
 *
 * - Renders nothing when `themeConfig.darkMode` is 'dark' or 'light'
 *   (i.e. when the mode is forced and the user has no say).
 * - Reads state from ThemeProvider via `useDarkMode()`.
 *
 * @example
 * // Drop it anywhere — Navbar, settings page, floating corner button, etc.
 * import { DarkModeToggle } from '../components/DarkModeToggle'
 * <DarkModeToggle />
 *
 * @example
 * // With custom sizing / positioning
 * <DarkModeToggle className="fixed bottom-4 right-4 p-2 shadow-lg" />
 */

import { Moon, Sun } from 'lucide-react'
import { useDarkMode } from '../lib/ThemeProvider'

interface DarkModeToggleProps {
  /** Extra Tailwind classes applied to the button wrapper. */
  className?: string
  /** Icon size in pixels. @default 16 */
  iconSize?:  number
}

export function DarkModeToggle({
  className = '',
  iconSize  = 16,
}: DarkModeToggleProps) {
  const { isDark, toggle, canToggle } = useDarkMode()

  // Hidden when mode is forced by theme.config.ts
  if (!canToggle) return null

  return (
    <button
      onClick={toggle}
      aria-label={isDark ? 'Passer en mode clair' : 'Passer en mode sombre'}
      title={isDark  ? 'Mode clair' : 'Mode sombre'}
      className={`
        p-1.5 rounded-md transition-colors duration-[var(--duration,200ms)]
        text-muted-foreground hover:text-foreground hover:bg-accent
        focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring
        ${className}
      `.trim()}
    >
      {isDark
        ? <Sun  width={iconSize} height={iconSize} />
        : <Moon width={iconSize} height={iconSize} />
      }
    </button>
  )
}
