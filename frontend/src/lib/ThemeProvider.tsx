/**
 * ThemeProvider
 * ─────────────────────────────────────────────────────────────────────────────
 * Reads theme.config.ts at startup and applies it to <html> via:
 *   - data-preset attribute   → CSS preset variable cascade
 *   - .dark class toggle      → dark/light mode switching
 *   - inline CSS variables    → brand colors / geometry / motion / fonts
 *
 * DARK MODE
 * ─────────
 * Behaviour depends on `themeConfig.darkMode`:
 *
 *   'auto'   User can toggle. Preference is saved to localStorage under "theme".
 *            Initial value resolved in order:
 *              1. localStorage("theme")  → 'dark' | 'light'
 *              2. prefers-color-scheme   → OS/browser setting
 *              3. DARK_PRESETS           → preset's native mode (fallback)
 *
 *   'dark'   Always dark. Toggle hidden.
 *
 *   'light'  Always light. Toggle hidden.
 *
 * CONSUMING DARK MODE
 * ───────────────────
 * Any component can read or change the mode:
 *
 *   import { useDarkMode } from '../lib/ThemeProvider'
 *
 *   const { isDark, toggle, canToggle } = useDarkMode()
 *
 *   // isDark    → boolean, current dark state
 *   // toggle    → () => void, flip dark/light (no-op if canToggle is false)
 *   // setDark   → (v: boolean) => void, set explicitly
 *   // canToggle → boolean, false when darkMode is 'dark' | 'light'
 */

import { createContext, useContext, useEffect, useState } from 'react'
import themeConfig, {
  DARK_PRESETS,
  GEOMETRY_RADIUS,
  MOTION_DURATION,
} from '../theme.config'
import type { DarkModeStrategy } from '../theme.config'

// ── Context ───────────────────────────────────────────────────────────────────

interface DarkModeContextValue {
  /** Current dark-mode state. */
  isDark:    boolean
  /** Flip dark/light. No-op when `canToggle` is false. */
  toggle:    () => void
  /** Set dark mode explicitly. No-op when `canToggle` is false. */
  setDark:   (v: boolean) => void
  /** False when darkMode is forced ('dark' | 'light'). Use to hide the toggle UI. */
  canToggle: boolean
}

const DarkModeContext = createContext<DarkModeContextValue>({
  isDark: false, toggle: () => {}, setDark: () => {}, canToggle: true,
})

/**
 * Hook — access dark mode state and controls from any component.
 *
 * @example
 * const { isDark, toggle, canToggle } = useDarkMode()
 * if (canToggle) <DarkModeToggle />
 */
export function useDarkMode(): DarkModeContextValue {
  return useContext(DarkModeContext)
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const LS_KEY = 'theme' as const

/**
 * Resolve the initial dark-mode boolean.
 * Order: strategy override → localStorage → OS preference → preset default.
 */
function resolveInitialDark(strategy: DarkModeStrategy): boolean {
  if (strategy === 'dark')  return true
  if (strategy === 'light') return false

  // 'auto': check explicit user preference first
  const stored = localStorage.getItem(LS_KEY)
  if (stored === 'dark')  return true
  if (stored === 'light') return false

  // Then OS/browser preference
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) return true

  // Final fallback: use the preset's native mode
  return DARK_PRESETS.has(themeConfig.preset)
}

// ── Provider ──────────────────────────────────────────────────────────────────

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const strategy  = themeConfig.darkMode ?? 'auto'
  const canToggle = strategy === 'auto'

  const [isDark, setIsDarkState] = useState<boolean>(
    () => resolveInitialDark(strategy)
  )

  // ── Apply .dark class + persist to localStorage ───────────────────────────
  useEffect(() => {
    const html = document.documentElement
    if (isDark) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }
    if (canToggle) {
      localStorage.setItem(LS_KEY, isDark ? 'dark' : 'light')
    }
  }, [isDark, canToggle])

  // ── Sync with OS preference changes (only when 'auto' + no explicit choice) ─
  useEffect(() => {
    if (!canToggle) return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    function handler(e: MediaQueryListEvent) {
      // Only follow system if user hasn't explicitly chosen
      if (!localStorage.getItem(LS_KEY)) {
        setIsDarkState(e.matches)
      }
    }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [canToggle])

  // ── Apply preset, colors, geometry, motion, fonts once ───────────────────
  useEffect(() => {
    const html = document.documentElement
    html.setAttribute('data-preset', themeConfig.preset)

    const s = html.style
    s.setProperty('--theme-primary',   themeConfig.colors.primary)
    s.setProperty('--theme-secondary', themeConfig.colors.secondary)
    s.setProperty('--theme-accent',    themeConfig.colors.accent)
    s.setProperty('--radius',          GEOMETRY_RADIUS[themeConfig.geometry])
    s.setProperty('--duration',        MOTION_DURATION[themeConfig.motion])
    s.setProperty('--font-heading',    themeConfig.fonts.heading)
    s.setProperty('--font-body',       themeConfig.fonts.body)
    s.setProperty('--font-mono',       themeConfig.fonts.mono)
  }, [])

  // ── Actions ───────────────────────────────────────────────────────────────
  function toggle() {
    if (!canToggle) return
    setIsDarkState(v => !v)
  }

  function setDark(v: boolean) {
    if (!canToggle) return
    setIsDarkState(v)
  }

  return (
    <DarkModeContext.Provider value={{ isDark, toggle, setDark, canToggle }}>
      {children}
    </DarkModeContext.Provider>
  )
}
