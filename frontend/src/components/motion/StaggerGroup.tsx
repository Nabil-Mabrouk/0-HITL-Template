/**
 * StaggerGroup + StaggerItem — Animation séquentielle des enfants.
 *
 * Le délai entre chaque enfant est contrôlé par STAGGER_DELAY[motionLevel]
 * dans lib/motion.ts. À 'none', tous les enfants apparaissent instantanément.
 *
 * @example
 * // Grid de features qui apparaît séquentiellement
 * <StaggerGroup className="grid grid-cols-3 gap-6">
 *   <StaggerItem><FeatureCard title="Fast" /></StaggerItem>
 *   <StaggerItem><FeatureCard title="Secure" /></StaggerItem>
 *   <StaggerItem><FeatureCard title="Scalable" /></StaggerItem>
 * </StaggerGroup>
 *
 * @example
 * // Liste de témoignages avec entrée décalée
 * <StaggerGroup className="flex flex-col gap-4">
 *   {testimonials.map(t => (
 *     <StaggerItem key={t.id}>
 *       <TestimonialCard {...t} />
 *     </StaggerItem>
 *   ))}
 * </StaggerGroup>
 */

import { useRef } from 'react'
import { motion, useInView } from 'framer-motion'
import { staggerContainerVariants, fadeInVariants } from '../../lib/motion'

interface StaggerGroupProps {
  children:   React.ReactNode
  className?: string
  /** Animer une seule fois (défaut: true) */
  once?:      boolean
  margin?:    string
}

export function StaggerGroup({
  children,
  className,
  once   = true,
  margin = '-80px',
}: StaggerGroupProps) {
  const ref    = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once, margin: margin as Parameters<typeof useInView>[1]['margin'] })

  return (
    <motion.div
      ref={ref}
      variants={staggerContainerVariants}
      initial="hidden"
      animate={inView ? 'visible' : 'hidden'}
      className={className}
    >
      {children}
    </motion.div>
  )
}

/**
 * StaggerItem — Enfant direct de StaggerGroup.
 * Hérite automatiquement du variant et du délai de son parent.
 */
export function StaggerItem({
  children,
  className,
}: {
  children:   React.ReactNode
  className?: string
}) {
  return (
    <motion.div variants={fadeInVariants} className={className}>
      {children}
    </motion.div>
  )
}
