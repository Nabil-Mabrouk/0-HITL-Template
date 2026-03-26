/**
 * NoiseOverlay
 * Film grain / noise texture overlay. Adds tactile depth without images.
 * SVG feTurbulence filter — zero JS, zero external assets.
 *
 * Combine with gradients or solid colors for the "premium grain" effect
 * popular in high-end editorial and luxury product sites.
 *
 * Usage:
 *   <section className="relative bg-background">
 *     <NoiseOverlay />
 *     <div className="relative z-10">... content ...</div>
 *   </section>
 *
 *   Or on a card:
 *   <div className="relative overflow-hidden rounded-lg bg-card p-6">
 *     <NoiseOverlay opacity={0.03} />
 *     content
 *   </div>
 *
 * Props:
 *   opacity     — 0–1  (default: 0.045)
 *   frequency   — grain fineness, 0.5–1.5  (default: 0.65)
 *   octaves     — complexity  (default: 4)
 */

import { useId } from 'react'
import { cn } from '../../lib/utils'

interface NoiseOverlayProps {
  className?: string
  opacity?: number
  frequency?: number
  octaves?: number
}

export function NoiseOverlay({
  className,
  opacity = 0.045,
  frequency = 0.65,
  octaves = 4,
}: NoiseOverlayProps) {
  const id = useId().replace(/:/g, '')

  return (
    <div
      className={cn('pointer-events-none absolute inset-0', className)}
      aria-hidden="true"
      style={{ opacity, mixBlendMode: 'overlay' }}
    >
      <svg
        className="h-full w-full"
        xmlns="http://www.w3.org/2000/svg"
      >
        <filter id={`noise-${id}`} x="0%" y="0%" width="100%" height="100%">
          <feTurbulence
            type="fractalNoise"
            baseFrequency={frequency}
            numOctaves={octaves}
            stitchTiles="stitch"
            result="noise"
          />
          <feColorMatrix
            type="saturate"
            values="0"
            in="noise"
            result="grey"
          />
          <feBlend in="SourceGraphic" in2="grey" mode="overlay" />
        </filter>
        <rect
          width="100%"
          height="100%"
          filter={`url(#noise-${id})`}
        />
      </svg>
    </div>
  )
}
