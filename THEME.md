# Theming Guide — 0-HITL Template

> **For AI agents**: This document is your complete brief for adapting this site's
> visual identity. You only need to edit **one file**: `frontend/src/theme.config.ts`.
> No component files require modification.

---

## How It Works in 30 Seconds

```
theme.config.ts
    └── ThemeProvider (reads config at startup)
            ├── sets html[data-preset="..."]     → activates a full CSS preset
            ├── toggles .dark class              → dark / light mode
            └── sets --theme-primary/secondary/accent → brand color overrides

presets/minimal.css    \
presets/vibrant.css     \   each redefines ALL 40+ shadcn/ui CSS variables
presets/glass.css       /   + component-level overrides (blur, shadows, borders)
presets/brutal.css     /
presets/editorial.css /

components/effects/    → drop-in visual primitives used in page sections
```

Changing `preset` in `theme.config.ts` is equivalent to swapping a complete
design system. Every button, card, input, and typography rule updates instantly.

---

## Quick Reference: What to Change for What Effect

| Goal | Change | Value |
|---|---|---|
| Dark developer tool | `preset` | `'minimal'` |
| Bright startup SaaS | `preset` | `'vibrant'` |
| Premium / immersive | `preset` | `'glass'` |
| Creative agency | `preset` | `'brutal'` |
| Newsletter / blog | `preset` | `'editorial'` |
| Shift brand hue | `colors.primary` | `oklch(62% 0.26 ‹hue›)` |
| More angular | `geometry` | `'sharp'` |
| More rounded | `geometry` | `'pill'` |
| No animations | `motion` | `'none'` |
| Living background | `effects.heroBackground` | `'glow-orbs'` |
| Technical background | `effects.heroBackground` | `'grid-dots'` |
| Grain texture | `effects.heroBackground` | `'noise'` |

---

## Color Hue Reference (oklch)

Use `oklch(lightness% chroma hue)`. Adjust only the hue to shift color family
while keeping the same perceived brightness and saturation.

```
Hue   0  — Red          crimson, urgency, energy
     25  — Orange        warmth, approachability, food
     55  — Amber/Gold    premium, achievement, fintech
     80  — Yellow        optimistic, creative tools
    120  — Green         eco, health, growth, money
    165  — Teal          calm, SaaS, productivity
    200  — Cyan          tech, water, clarity
    220  — Sky Blue      trust, corporate, banking
    264  — Indigo        developer tools (DEFAULT)
    280  — Purple        AI, creativity, magic
    310  — Violet        luxury, beauty, fashion
    340  — Pink          consumer, playful, social
```

Examples:
```typescript
// Fintech / trust
colors: { primary: 'oklch(50% 0.20 220)', secondary: 'oklch(45% 0.18 200)', accent: 'oklch(72% 0.16 55)' }

// Health / calm
colors: { primary: 'oklch(52% 0.20 165)', secondary: 'oklch(56% 0.18 120)', accent: 'oklch(65% 0.15 80)' }

// AI / creative
colors: { primary: 'oklch(62% 0.28 280)', secondary: 'oklch(58% 0.27 310)', accent: 'oklch(70% 0.22 55)' }

// Eco / sustainability
colors: { primary: 'oklch(50% 0.22 145)', secondary: 'oklch(54% 0.20 120)', accent: 'oklch(68% 0.18 80)' }

// Luxury / premium
colors: { primary: 'oklch(72% 0.10 80)',  secondary: 'oklch(45% 0.05 60)',  accent: 'oklch(76% 0.12 55)' }
```

---

## Preset + Effect Combinations That Work

These are validated visual identities ready to use as starting points:

### Technical SaaS (Linear / Vercel style)
```typescript
preset: 'minimal',
colors: { primary: 'oklch(62.8% 0.258 264)', secondary: 'oklch(58% 0.27 310)', accent: 'oklch(74% 0.18 55)' },
effects: { heroBackground: 'glow-orbs', cardStyle: 'elevated', buttonStyle: 'filled' },
```

### Startup Landing Page (Framer / Resend style)
```typescript
preset: 'vibrant',
colors: { primary: 'oklch(58% 0.27 264)', secondary: 'oklch(62% 0.28 310)', accent: 'oklch(72% 0.20 25)' },
effects: { heroBackground: 'mesh-gradient', cardStyle: 'elevated', buttonStyle: 'gradient' },
```

### AI Product (mystical, premium)
```typescript
preset: 'glass',
colors: { primary: 'oklch(65% 0.28 280)', secondary: 'oklch(60% 0.26 310)', accent: 'oklch(74% 0.18 55)' },
effects: { heroBackground: 'glow-orbs', cardStyle: 'glass', buttonStyle: 'gradient' },
```

### Creative Agency (neobrutalist)
```typescript
preset: 'brutal',
colors: { primary: 'oklch(60% 0.28 25)', secondary: 'oklch(55% 0.26 25)', accent: 'oklch(80% 0.20 80)' },
geometry: 'sharp',
effects: { heroBackground: 'grid-dots', cardStyle: 'bordered', buttonStyle: 'brutal' },
```

### Newsletter / Knowledge Base (editorial)
```typescript
preset: 'editorial',
colors: { primary: 'oklch(40% 0.12 264)', secondary: 'oklch(45% 0.12 200)', accent: 'oklch(55% 0.18 30)' },
fonts: { heading: 'Georgia, "Playfair Display", serif', body: '"Inter", sans-serif', mono: '"JetBrains Mono", monospace' },
effects: { heroBackground: 'noise', cardStyle: 'bordered', buttonStyle: 'filled' },
```

---

## Using Effect Components in Pages

Import from `@/components/effects`:

```tsx
import { GlowOrbs, MeshGradient, GridDots, NoiseOverlay, AnimatedBorder } from '@/components/effects'
```

### Background effects (always use inside `relative overflow-hidden`)

```tsx
// Hero section with glow orbs (dark presets)
<section className="relative min-h-screen overflow-hidden">
  <GlowOrbs intensity="normal" count={3} />
  <div className="relative z-10">
    <h1>Your headline</h1>
  </div>
</section>

// Section with animated mesh gradient
<section className="relative overflow-hidden bg-background py-32">
  <MeshGradient opacity={0.4} speed="slow" />
  <div className="relative z-10">content</div>
</section>

// Technical grid for feature sections
<section className="relative overflow-hidden py-24">
  <GridDots variant="dots" size={32} opacity={0.3} />
  <div className="relative z-10">content</div>
</section>

// Grain texture (editorial / luxury)
<section className="relative overflow-hidden bg-background py-20">
  <NoiseOverlay opacity={0.04} />
  <div className="relative z-10">content</div>
</section>
```

### AnimatedBorder (wrap elements, not sections)

```tsx
// Highlight a CTA button
<AnimatedBorder rounded="md">
  <Button size="lg">Get Started Free</Button>
</AnimatedBorder>

// Featured pricing card
<AnimatedBorder rounded="lg" padding={2}>
  <Card className="p-8">
    <Badge>Most Popular</Badge>
    <h3>Pro Plan</h3>
  </Card>
</AnimatedBorder>
```

---

## Typography Pairings

If loading Google Fonts, add `<link>` to `index.html`. Then set in `theme.config.ts`:

| Personality | `fonts.heading` | `fonts.body` |
|---|---|---|
| Technical precision | `'"Geist Variable", sans-serif'` | `'"Geist Variable", sans-serif'` |
| Startup / bold | `'"Cal Sans", "Sora", sans-serif'` | `'"DM Sans", sans-serif'` |
| Premium / editorial | `'Georgia, "Playfair Display", serif'` | `'"Inter", sans-serif'` |
| Geometric / clean | `'"Outfit", sans-serif'` | `'"Outfit", sans-serif'` |
| Humanist / friendly | `'"Plus Jakarta Sans", sans-serif'` | `'"Plus Jakarta Sans", sans-serif'` |

---

## Geometry × Preset Matrix

Not all combinations work equally well. Recommended:

| Preset | `sharp` | `soft` | `rounded` | `pill` |
|---|---|---|---|---|
| minimal | ✓ excellent | ✓ good | ✓ default | — |
| vibrant | — | ✓ good | ✓ default | ✓ playful |
| glass | — | — | ✓ default | ✓ good |
| brutal | ✓ required | — | — | — |
| editorial | ✓ good | ✓ default | ✓ acceptable | — |

---

## Do / Don't for AI Agents

**DO:**
- Edit only `frontend/src/theme.config.ts` for visual changes
- Use effect components by importing from `@/components/effects`
- Apply `relative overflow-hidden` to any section that hosts a background effect
- Use `oklch()` color syntax — it handles perceptual uniformity automatically
- Pair `preset: 'brutal'` with `geometry: 'sharp'` (they are inseparable)

**DON'T:**
- Edit individual shadcn/ui components (`button.tsx`, `card.tsx`, etc.) to change colors
- Hardcode colors in component files — always use CSS variables (`var(--primary)`, etc.)
- Mix a light preset with `GlowOrbs` at high intensity — the orbs are designed for dark backgrounds
- Use `MeshGradient` and `GlowOrbs` in the same section — choose one per section
- Set `motion: 'playful'` with `preset: 'editorial'` — the personalities conflict
