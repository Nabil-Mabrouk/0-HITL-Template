/**
 * MeshGradient
 * Animated CSS gradient mesh — smooth, organic, living background.
 * Pure CSS, zero canvas, excellent performance.
 *
 * Usage:
 *   <section className="relative overflow-hidden">
 *     <MeshGradient />
 *     <div className="relative z-10">... content ...</div>
 *   </section>
 *
 * Props:
 *   speed     — 'slow' | 'normal' | 'fast'  (default: 'slow')
 *   opacity   — 0–1  (default: 0.6)
 */

import { cn } from '../../lib/utils'

type Speed = 'slow' | 'normal' | 'fast'

interface MeshGradientProps {
  className?: string
  speed?: Speed
  opacity?: number
}

const durationMap: Record<Speed, [string, string, string]> = {
  slow:   ['16s', '22s', '28s'],
  normal: ['10s', '14s', '18s'],
  fast:   ['6s',  '9s',  '12s'],
}

export function MeshGradient({
  className,
  speed = 'slow',
  opacity = 0.6,
}: MeshGradientProps) {
  const [d1, d2, d3] = durationMap[speed]

  return (
    <div
      className={cn('pointer-events-none absolute inset-0 overflow-hidden', className)}
      aria-hidden="true"
      style={{ opacity }}
    >
      {/* Layer 1 — primary blob, drifts slowly */}
      <div
        className="absolute inset-0"
        style={{
          background: `
            radial-gradient(ellipse 65% 55% at 15% 25%,
              var(--theme-primary,   oklch(62.8% 0.258 264)) 0%,
              transparent 70%)
          `,
          animation: `mesh-a ${d1} ease-in-out infinite alternate`,
        }}
      />

      {/* Layer 2 — secondary blob, counter-drifts */}
      <div
        className="absolute inset-0"
        style={{
          background: `
            radial-gradient(ellipse 55% 60% at 80% 20%,
              var(--theme-secondary, oklch(58% 0.27 310)) 0%,
              transparent 70%)
          `,
          animation: `mesh-b ${d2} ease-in-out infinite alternate`,
        }}
      />

      {/* Layer 3 — accent blob, bottom center */}
      <div
        className="absolute inset-0"
        style={{
          background: `
            radial-gradient(ellipse 70% 45% at 45% 90%,
              var(--theme-accent, oklch(74% 0.18 55)) 0%,
              transparent 65%)
          `,
          animation: `mesh-c ${d3} ease-in-out infinite alternate`,
        }}
      />

      <style>{`
        @keyframes mesh-a {
          from { transform: translate(0%,   0%)   scale(1);    }
          to   { transform: translate(6%,   8%)   scale(1.12); }
        }
        @keyframes mesh-b {
          from { transform: translate(0%,   0%)   scale(1);    }
          to   { transform: translate(-8%,  5%)   scale(1.08); }
        }
        @keyframes mesh-c {
          from { transform: translate(0%,   0%)   scale(1);    }
          to   { transform: translate(5%,  -6%)   scale(1.10); }
        }
      `}</style>
    </div>
  )
}
