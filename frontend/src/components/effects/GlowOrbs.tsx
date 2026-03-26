/**
 * GlowOrbs
 * Blurred radial blobs in brand colors. The defining visual of modern dark SaaS.
 *
 * Usage:
 *   <section className="relative overflow-hidden">
 *     <GlowOrbs />
 *     <div className="relative z-10">... content ...</div>
 *   </section>
 *
 * Props:
 *   intensity  — 'soft' | 'normal' | 'vivid'  (default: 'normal')
 *   count      — 2 | 3 | 4  (default: 3)
 *   animated   — enable subtle drift animation  (default: true)
 */

import { cn } from '../../lib/utils'

type Intensity = 'soft' | 'normal' | 'vivid'

interface GlowOrbsProps {
  className?: string
  intensity?: Intensity
  count?: 2 | 3 | 4
  animated?: boolean
}

const opacityMap: Record<Intensity, [number, number, number, number]> = {
  soft:   [0.15, 0.10, 0.08, 0.06],
  normal: [0.25, 0.18, 0.12, 0.08],
  vivid:  [0.40, 0.28, 0.18, 0.12],
}

export function GlowOrbs({
  className,
  intensity = 'normal',
  count = 3,
  animated = true,
}: GlowOrbsProps) {
  const [op1, op2, op3, op4] = opacityMap[intensity]

  return (
    <div
      className={cn('pointer-events-none absolute inset-0 overflow-hidden', className)}
      aria-hidden="true"
    >
      {/* Primary orb — upper left */}
      <div
        className={cn(
          'absolute -top-[20%] -left-[5%] h-[600px] w-[600px] rounded-full blur-[120px]',
          animated && 'animate-[orb-drift-a_12s_ease-in-out_infinite]',
        )}
        style={{
          background: 'var(--theme-primary, oklch(62.8% 0.258 264))',
          opacity: op1,
        }}
      />

      {/* Secondary orb — upper right */}
      {count >= 2 && (
        <div
          className={cn(
            'absolute -top-[10%] right-[5%] h-[500px] w-[500px] rounded-full blur-[100px]',
            animated && 'animate-[orb-drift-b_15s_ease-in-out_infinite]',
          )}
          style={{
            background: 'var(--theme-secondary, oklch(58% 0.27 310))',
            opacity: op2,
          }}
        />
      )}

      {/* Accent orb — lower center */}
      {count >= 3 && (
        <div
          className={cn(
            'absolute bottom-[-15%] left-[25%] h-[400px] w-[700px] rounded-full blur-[140px]',
            animated && 'animate-[orb-drift-c_18s_ease-in-out_infinite]',
          )}
          style={{
            background: 'var(--theme-accent, oklch(74% 0.18 55))',
            opacity: op3,
          }}
        />
      )}

      {/* Fourth orb — lower right */}
      {count >= 4 && (
        <div
          className={cn(
            'absolute bottom-[10%] right-[-5%] h-[350px] w-[350px] rounded-full blur-[90px]',
            animated && 'animate-[orb-drift-d_20s_ease-in-out_infinite]',
          )}
          style={{
            background: 'var(--theme-primary, oklch(62.8% 0.258 264))',
            opacity: op4,
          }}
        />
      )}

      {/* Keyframe animations injected once */}
      <style>{`
        @keyframes orb-drift-a {
          0%, 100% { transform: translate(0%, 0%) scale(1);    }
          40%       { transform: translate(4%, 6%) scale(1.08); }
          70%       { transform: translate(-3%, 3%) scale(0.96);}
        }
        @keyframes orb-drift-b {
          0%, 100% { transform: translate(0%, 0%) scale(1);     }
          35%       { transform: translate(-5%, 4%) scale(1.06); }
          65%       { transform: translate(3%, -3%) scale(0.94); }
        }
        @keyframes orb-drift-c {
          0%, 100% { transform: translate(0%, 0%) scale(1);    }
          50%       { transform: translate(3%, -5%) scale(1.05);}
        }
        @keyframes orb-drift-d {
          0%, 100% { transform: translate(0%, 0%) scale(1);    }
          45%       { transform: translate(-4%, 3%) scale(1.1); }
        }
      `}</style>
    </div>
  )
}
