/**
 * FadeIn — Apparition au scroll avec fondu + translation verticale.
 *
 * L'animation se déclenche quand l'élément entre dans le viewport.
 * Respecte automatiquement le niveau de motion défini dans theme.config.ts.
 *
 * @example
 * // Utilisation simple
 * <FadeIn>
 *   <FeatureCard />
 * </FadeIn>
 *
 * @example
 * // Avec délai (pour décaler manuellement sans StaggerGroup)
 * <FadeIn delay={0.2}>
 *   <HeroText />
 * </FadeIn>
 *
 * @example
 * // Rejouer à chaque fois que l'élément quitte/entre dans le viewport
 * <FadeIn once={false}>
 *   <AnimatedStat />
 * </FadeIn>
 */

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import type { UseInViewOptions } from 'framer-motion'
import { fadeInVariants } from '../../lib/motion'

interface FadeInProps {
  children:   React.ReactNode
  /** Délai avant le début de l'animation (secondes) */
  delay?:     number
  /** Classe CSS appliquée au wrapper */
  className?: string
  /** Animer une seule fois (défaut: true) */
  once?:      boolean
  /** Marge avant déclenchement — négatif = déclenche avant d'atteindre l'élément */
  margin?:    UseInViewOptions['margin']
}

export function FadeIn({
  children,
  delay   = 0,
  className,
  once    = true,
  margin  = '-60px' as UseInViewOptions['margin'],
}: FadeInProps) {
  const ref    = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once, margin })

  const variants = delay > 0
    ? {
        ...fadeInVariants,
        visible: {
          ...fadeInVariants.visible,
          transition: {
            ...(fadeInVariants.visible.transition as object),
            delay,
          },
        },
      }
    : fadeInVariants

  return (
    <motion.div
      ref={ref}
      variants={variants}
      initial="hidden"
      animate={inView ? 'visible' : 'hidden'}
      className={className}
    >
      {children}
    </motion.div>
  )
}
