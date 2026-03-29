/**
 * ╔══════════════════════════════════════════════════════════════════════════╗
 * ║  THEME CONFIGURATION — Single source of truth for visual identity.      ║
 * ║                                                                          ║
 * ║  HOW TO RESTYLE THIS SITE (for Claude Code / AI agents):                ║
 * ║  ────────────────────────────────────────────────────────               ║
 * ║  1. Change `preset` — this alone transforms the entire visual language. ║
 * ║  2. Override `colors` to set your brand palette.                        ║
 * ║  3. Change `fonts.heading` for personality (serif = editorial, etc.)    ║
 * ║  4. Adjust `geometry` for edge roundness and `motion` for animations.   ║
 * ║  5. Set `effects.heroBackground` for the landing page visual.           ║
 * ║                                                                          ║
 * ║  That is all. No component files need to be touched.                    ║
 * ╚══════════════════════════════════════════════════════════════════════════╝
 */

// ── Type Definitions ──────────────────────────────────────────────────────────

/**
 * AVAILABLE PRESETS — each is a complete, opinionated visual identity:
 *
 *  'minimal'   Dark, refined, monochromatic. Developer tools, technical SaaS.
 *              Inspired by: Linear, Vercel, Raycast.
 *
 *  'vibrant'   Light background, gradient-heavy, high energy.
 *              Inspired by: Framer, Lemon Squeezy, Resend.
 *
 *  'glass'     Dark base, frosted glass surfaces, depth through blur.
 *              Inspired by: Apple visionOS, gaming dashboards.
 *
 *  'brutal'    Zero radius, thick borders, hard shadows. Raw and intentional.
 *              Inspired by: brutalist web design, creative agencies.
 *
 *  'editorial' Warm paper tones, serif headings, generous whitespace.
 *              Inspired by: Substack, Notion, literary magazines.
 */
export type ThemePreset = 'minimal' | 'vibrant' | 'glass' | 'brutal' | 'editorial'

/**
 * DARK MODE STRATEGY — controls how dark/light mode is determined at runtime.
 *
 *  'auto'   User can toggle dark/light with the button in the Navbar.
 *           Preference is saved in localStorage under the key "theme".
 *           Initial value resolves in this order:
 *             1. localStorage  (explicit user choice)
 *             2. prefers-color-scheme  (OS/browser setting)
 *             3. Preset's native mode  (DARK_PRESETS below)
 *
 *  'dark'   Always dark. Toggle button is hidden.
 *
 *  'light'  Always light. Toggle button is hidden.
 *
 * NOTE: When set to 'auto', the toggle button appears automatically in the
 * Navbar. No other code changes are needed.
 */
export type DarkModeStrategy = 'auto' | 'dark' | 'light'

/**
 * GEOMETRY — controls border-radius across the entire UI.
 *  'sharp'   0px  — Angular, technical, brutalist.
 *  'soft'    4px  — Minimal curvature, modern SaaS.
 *  'rounded' 8px  — Friendly, approachable.
 *  'pill'    24px — Playful, consumer app.
 */
export type Geometry = 'sharp' | 'soft' | 'rounded' | 'pill'

/**
 * MOTION — controls animation intensity everywhere.
 *  'none'    No animations (accessibility-first, fastest).
 *  'subtle'  Micro-interactions only (opacity, slight scale).
 *  'smooth'  Standard transitions and entrance animations.
 *  'playful' Bouncy springs, expressive stagger effects.
 */
export type Motion = 'none' | 'subtle' | 'smooth' | 'playful'

/**
 * HERO BACKGROUND — visual effect behind the landing page hero section.
 * Use the matching component from `components/effects/`:
 *  'none'          Plain background color from active preset.
 *  'glow-orbs'     Blurred radial blobs (classic dark SaaS look).    → <GlowOrbs />
 *  'mesh-gradient' Animated CSS gradient mesh.                       → <MeshGradient />
 *  'grid-dots'     Dot grid pattern, technical feel.                 → <GridDots />
 *  'noise'         Grain texture overlay.                            → <NoiseOverlay />
 */
export type HeroBg = 'none' | 'glow-orbs' | 'mesh-gradient' | 'grid-dots' | 'noise'

/**
 * CARD STYLE — visual treatment for content cards.
 *  'flat'     No shadow, no border. Color contrast only.
 *  'elevated' Subtle drop shadow (default).
 *  'bordered' Explicit border, no shadow.
 *  'glass'    Backdrop blur + semi-transparent surface.
 */
export type CardStyle = 'flat' | 'elevated' | 'bordered' | 'glass'

/**
 * BUTTON STYLE — personality of primary action buttons.
 *  'filled'    Solid primary color fill (default).
 *  'outlined'  Border only, no fill.
 *  'gradient'  Linear gradient from primary to secondary.
 *  'brutal'    Solid fill + hard offset shadow, no radius.
 */
export type ButtonStyle = 'filled' | 'outlined' | 'gradient' | 'brutal'

export interface ThemeConfig {
  preset:    ThemePreset
  /**
   * Dark mode strategy.
   * - 'auto'   → system preference + user toggle (saved to localStorage)
   * - 'dark'   → force dark, toggle hidden
   * - 'light'  → force light, toggle hidden
   * @default 'auto'
   */
  darkMode?: DarkModeStrategy
  colors: {
    /** Main brand color — buttons, links, accents. Use oklch() for vivid results. */
    primary:   string
    /** Gradient partner — used in mesh gradients, hover states. */
    secondary: string
    /** Highlight color — badges, underlines, notifications. */
    accent:    string
  }
  fonts: {
    /** Heading font — has the most visual impact on personality. */
    heading: string
    /** Body font — should be highly readable. */
    body:    string
    /** Monospace font — for code blocks and technical content. */
    mono:    string
  }
  geometry: Geometry
  motion:   Motion
  effects: {
    heroBackground: HeroBg
    cardStyle:      CardStyle
    buttonStyle:    ButtonStyle
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// ▼▼▼  EDIT BELOW TO RESTYLE THE SITE  ▼▼▼
// ─────────────────────────────────────────────────────────────────────────────

const themeConfig: ThemeConfig = {

  // ── Choose a preset ────────────────────────────────────────────────────────
  // 'minimal' | 'vibrant' | 'glass' | 'brutal' | 'editorial'
  preset: 'minimal',

  // ── Dark mode strategy ─────────────────────────────────────────────────────
  // 'auto'  → user can toggle (OS preference + localStorage)
  // 'dark'  → always dark, no toggle
  // 'light' → always light, no toggle
  darkMode: 'auto',

  // ── Brand colors ───────────────────────────────────────────────────────────
  // oklch(lightness chroma hue) — adjust hue to shift across the spectrum:
  //   0=red  30=orange  60=yellow  120=green  200=teal  264=indigo  310=violet
  //
  // EXAMPLES BY INDUSTRY:
  //   Fintech / Trust:   oklch(50% 0.20 230)  — deep blue
  //   Health / Calm:     oklch(55% 0.18 165)  — teal
  //   Energy / Bold:     oklch(60% 0.28  30)  — orange
  //   Creative / Fun:    oklch(65% 0.30 310)  — violet
  //   Eco / Growth:      oklch(52% 0.22 145)  — green
  //   Luxury / Premium:  oklch(72% 0.08  80)  — gold
  colors: {
    primary:   'oklch(62.8% 0.258 264)',   // indigo
    secondary: 'oklch(58%   0.27  310)',   // violet
    accent:    'oklch(74%   0.18   55)',   // amber
  },

  // ── Typography ─────────────────────────────────────────────────────────────
  // PERSONALITY PAIRINGS:
  //   Technical SaaS:  heading: '"Geist Variable", sans-serif'
  //   Startup / Bold:  heading: '"Cal Sans", "Sora", sans-serif'
  //   Editorial:       heading: 'Georgia, "Playfair Display", serif'
  //   Humanist:        heading: '"DM Sans", sans-serif'
  //   Geometric:       heading: '"Outfit", "Nunito", sans-serif'
  fonts: {
    heading: '"Geist Variable", system-ui, sans-serif',
    body:    '"Geist Variable", system-ui, sans-serif',
    mono:    '"Geist Mono", "JetBrains Mono", ui-monospace, monospace',
  },

  // ── Shape & motion ─────────────────────────────────────────────────────────
  geometry: 'rounded',  // 'sharp' | 'soft' | 'rounded' | 'pill'
  motion:   'smooth',   // 'none' | 'subtle' | 'smooth' | 'playful'

  // ── Visual effects ─────────────────────────────────────────────────────────
  effects: {
    heroBackground: 'glow-orbs',  // 'none' | 'glow-orbs' | 'mesh-gradient' | 'grid-dots' | 'noise'
    cardStyle:      'elevated',   // 'flat' | 'elevated' | 'bordered' | 'glass'
    buttonStyle:    'filled',     // 'filled' | 'outlined' | 'gradient' | 'brutal'
  },

}

// ─────────────────────────────────────────────────────────────────────────────
// ▲▲▲  END OF EDITABLE SECTION  ▲▲▲
// ─────────────────────────────────────────────────────────────────────────────

export default themeConfig

/** Presets that use dark mode by default. */
export const DARK_PRESETS: ReadonlySet<ThemePreset> = new Set(['minimal', 'glass', 'brutal'])

/** Radius values for each geometry setting. */
export const GEOMETRY_RADIUS: Record<Geometry, string> = {
  sharp:   '0rem',
  soft:    '0.25rem',
  rounded: '0.5rem',
  pill:    '1.5rem',
}

/** Transition duration for each motion setting. */
export const MOTION_DURATION: Record<Motion, string> = {
  none:    '0ms',
  subtle:  '100ms',
  smooth:  '220ms',
  playful: '350ms',
}
