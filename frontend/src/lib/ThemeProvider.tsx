/**
 * ThemeProvider
 * Reads theme.config.ts at startup and applies it to <html> via:
 *   - data-preset attribute  → CSS preset variables cascade
 *   - .dark class toggle     → dark/light mode
 *   - inline CSS variables   → brand color / geometry / motion overrides
 */
import { useEffect } from 'react'
import themeConfig, {
  DARK_PRESETS,
  GEOMETRY_RADIUS,
  MOTION_DURATION,
} from '../theme.config'

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const html = document.documentElement

    // 1. Apply preset — CSS preset files target html[data-preset="..."]
    html.setAttribute('data-preset', themeConfig.preset)

    // 2. Toggle dark class based on preset personality
    if (DARK_PRESETS.has(themeConfig.preset)) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }

    // 3. Brand color overrides — presets read these via var(--theme-primary)
    const s = html.style
    s.setProperty('--theme-primary',   themeConfig.colors.primary)
    s.setProperty('--theme-secondary', themeConfig.colors.secondary)
    s.setProperty('--theme-accent',    themeConfig.colors.accent)

    // 4. Geometry — overrides --radius used by all shadcn/ui components
    s.setProperty('--radius', GEOMETRY_RADIUS[themeConfig.geometry])

    // 5. Motion — CSS transition duration token
    s.setProperty('--duration', MOTION_DURATION[themeConfig.motion])

    // 6. Font heading — applied via CSS variable so headings pick it up
    s.setProperty('--font-heading', themeConfig.fonts.heading)
    s.setProperty('--font-body',    themeConfig.fonts.body)
    s.setProperty('--font-mono',    themeConfig.fonts.mono)
  }, [])

  return <>{children}</>
}
