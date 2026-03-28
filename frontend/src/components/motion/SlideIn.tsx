/**
 * SlideIn — Glissement depuis une direction au scroll.
 *
 * Idéal pour les sections "deux colonnes" (texte à gauche / image à droite)
 * ou les éléments latéraux qui surgissent depuis les bords.
 *
 * @example
 * // Section features : texte depuis la gauche, visuel depuis la droite
 * <div className="grid grid-cols-2 gap-12">
 *   <SlideIn from="left">
 *     <FeatureText />
 *   </SlideIn>
 *   <SlideIn from="right" delay={0.1}>
 *     <FeatureVisual />
 *   </SlideIn>
 * </div>
 *
 * @example
 * // Titre qui descend du haut
 * <SlideIn from="up">
 *   <h2>Notre méthode</h2>
 * </SlideIn>
 */

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import { slideInVariants } from '../../lib/motion'

interface SlideInProps {
  children:   React.ReactNode
  from?:      'left' | 'right' | 'up' | 'down'
  delay?:     number
  className?: string
  once?:      boolean
  margin?:    string
}

export function SlideIn({
  children,
  from    = 'left',
  delay   = 0,
  className,
  once    = true,
  margin  = '-60px',
}: SlideInProps) {
  const ref      = useRef<HTMLDivElement>(null)
  const inView   = useInView(ref, { once, margin: margin as Parameters<typeof useInView>[1]['margin'] })
  const variants = slideInVariants(from)

  const resolvedVariants = delay > 0
    ? {
        ...variants,
        visible: {
          ...variants.visible,
          transition: {
            ...(variants.visible.transition as object),
            delay,
          },
        },
      }
    : variants

  return (
    <motion.div
      ref={ref}
      variants={resolvedVariants}
      initial="hidden"
      animate={inView ? 'visible' : 'hidden'}
      className={className}
    >
      {children}
    </motion.div>
  )
}
