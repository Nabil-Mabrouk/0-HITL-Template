/**
 * AnimatedBorder
 * Wraps any element with a rotating conic gradient border.
 * Great for hero CTAs, featured cards, premium badges.
 *
 * Usage:
 *   <AnimatedBorder>
 *     <Button>Get Started</Button>
 *   </AnimatedBorder>
 *
 *   <AnimatedBorder rounded="lg" padding={2}>
 *     <Card>Featured plan</Card>
 *   </AnimatedBorder>
 *
 * Props:
 *   active    — turn the animation on/off  (default: true)
 *   speed     — 'slow' | 'normal' | 'fast'  (default: 'normal')
 *   rounded   — border radius preset: 'sm'|'md'|'lg'|'xl'|'full'|'none'
 *   padding   — gap between border and content in px  (default: 1)
 */

import { cn } from '../../lib/utils'

type Speed   = 'slow' | 'normal' | 'fast'
type Rounded = 'none' | 'sm' | 'md' | 'lg' | 'xl' | 'full'

interface AnimatedBorderProps {
  children: React.ReactNode
  className?: string
  active?: boolean
  speed?: Speed
  rounded?: Rounded
  padding?: number
}

const durationMap: Record<Speed, string> = {
  slow:   '4s',
  normal: '2.5s',
  fast:   '1.2s',
}

const radiusMap: Record<Rounded, string> = {
  none: '0px',
  sm:   'calc(var(--radius) * 0.6)',
  md:   'calc(var(--radius) * 0.8)',
  lg:   'var(--radius)',
  xl:   'calc(var(--radius) * 1.4)',
  full: '9999px',
}

export function AnimatedBorder({
  children,
  className,
  active = true,
  speed = 'normal',
  rounded = 'md',
  padding = 1,
}: AnimatedBorderProps) {
  const radius = radiusMap[rounded]
  const duration = durationMap[speed]

  return (
    <div
      className={cn('relative inline-flex', className)}
      style={{ borderRadius: radius, padding: active ? `${padding}px` : 0 }}
    >
      {/* The animated gradient border layer */}
      {active && (
        <>
          <div
            className="absolute inset-0"
            style={{
              borderRadius: `calc(${radius} + ${padding}px)`,
              background: `conic-gradient(
                from var(--border-angle, 0deg),
                var(--theme-primary,   oklch(62.8% 0.258 264)),
                var(--theme-secondary, oklch(58% 0.27 310)),
                var(--theme-accent,    oklch(74% 0.18 55)),
                var(--theme-primary,   oklch(62.8% 0.258 264))
              )`,
              animation: `border-rotate ${duration} linear infinite`,
            }}
          />
          {/* Blurred glow version beneath */}
          <div
            className="absolute inset-0 blur-[6px]"
            style={{
              borderRadius: `calc(${radius} + ${padding}px)`,
              background: `conic-gradient(
                from var(--border-angle, 0deg),
                var(--theme-primary,   oklch(62.8% 0.258 264)),
                var(--theme-secondary, oklch(58% 0.27 310)),
                var(--theme-accent,    oklch(74% 0.18 55)),
                var(--theme-primary,   oklch(62.8% 0.258 264))
              )`,
              opacity: 0.5,
              animation: `border-rotate ${duration} linear infinite`,
            }}
          />
        </>
      )}

      {/* Content layer sits above the border */}
      <div
        className="relative z-10 bg-card"
        style={{ borderRadius: radius }}
      >
        {children}
      </div>

      <style>{`
        @keyframes border-rotate {
          from { --border-angle: 0deg;   }
          to   { --border-angle: 360deg; }
        }
        @property --border-angle {
          syntax:       '<angle>';
          initial-value: 0deg;
          inherits:     false;
        }
      `}</style>
    </div>
  )
}
