/**
 * GridDots
 * Dot grid or line grid background. Technical, clean, precise.
 * SVG-based, zero JavaScript, scales to any container.
 *
 * Usage:
 *   <section className="relative">
 *     <GridDots />
 *     <div className="relative z-10">... content ...</div>
 *   </section>
 *
 * Props:
 *   variant   — 'dots' | 'lines' | 'cross'  (default: 'dots')
 *   size      — grid cell size in px  (default: 28)
 *   opacity   — 0–1  (default: 0.35)
 *   fade      — add radial fade towards edges  (default: true)
 */

import { useId } from 'react'
import { cn } from '../../lib/utils'

type Variant = 'dots' | 'lines' | 'cross'

interface GridDotsProps {
  className?: string
  variant?: Variant
  size?: number
  opacity?: number
  fade?: boolean
}

export function GridDots({
  className,
  variant = 'dots',
  size = 28,
  opacity = 0.35,
  fade = true,
}: GridDotsProps) {
  const id = useId()
  const maskId = `grid-fade-${id.replace(/:/g, '')}`
  const patternId = `grid-pattern-${id.replace(/:/g, '')}`
  const dotR = size * 0.055
  const strokeW = size * 0.04

  return (
    <div
      className={cn('pointer-events-none absolute inset-0', className)}
      aria-hidden="true"
    >
      <svg
        className="absolute inset-0 h-full w-full"
        xmlns="http://www.w3.org/2000/svg"
        style={{ opacity }}
      >
        <defs>
          <pattern
            id={patternId}
            width={size}
            height={size}
            patternUnits="userSpaceOnUse"
          >
            {variant === 'dots' && (
              <circle
                cx={size / 2}
                cy={size / 2}
                r={dotR}
                fill="currentColor"
              />
            )}

            {variant === 'lines' && (
              <>
                <line
                  x1={0} y1={size / 2}
                  x2={size} y2={size / 2}
                  stroke="currentColor"
                  strokeWidth={strokeW}
                />
                <line
                  x1={size / 2} y1={0}
                  x2={size / 2} y2={size}
                  stroke="currentColor"
                  strokeWidth={strokeW}
                />
              </>
            )}

            {variant === 'cross' && (
              <>
                {/* Small cross at each intersection */}
                <line
                  x1={size / 2 - dotR * 3} y1={size / 2}
                  x2={size / 2 + dotR * 3} y2={size / 2}
                  stroke="currentColor"
                  strokeWidth={strokeW}
                />
                <line
                  x1={size / 2} y1={size / 2 - dotR * 3}
                  x2={size / 2} y2={size / 2 + dotR * 3}
                  stroke="currentColor"
                  strokeWidth={strokeW}
                />
              </>
            )}
          </pattern>

          {fade && (
            <radialGradient id={maskId} cx="50%" cy="50%" r="55%">
              <stop offset="0%"   stopColor="white" stopOpacity="1" />
              <stop offset="70%"  stopColor="white" stopOpacity="0.6" />
              <stop offset="100%" stopColor="white" stopOpacity="0" />
            </radialGradient>
          )}
        </defs>

        {fade ? (
          <>
            <mask id={`${maskId}-mask`}>
              <rect width="100%" height="100%" fill={`url(#${maskId})`} />
            </mask>
            <rect
              width="100%"
              height="100%"
              fill={`url(#${patternId})`}
              mask={`url(#${maskId}-mask)`}
            />
          </>
        ) : (
          <rect width="100%" height="100%" fill={`url(#${patternId})`} />
        )}
      </svg>
    </div>
  )
}
