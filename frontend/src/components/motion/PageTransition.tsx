/**
 * PageTransition — Enveloppe une page pour l'animer lors des changements de route.
 *
 * Doit être utilisé avec <AnimatePresence> dans App.tsx (déjà configuré).
 * Envelopper le contenu racine de chaque page dans ce composant pour obtenir
 * des transitions fluides entre les routes.
 *
 * @example
 * // Dans Landing.tsx
 * export default function Landing() {
 *   return (
 *     <PageTransition>
 *       <main>...</main>
 *     </PageTransition>
 *   )
 * }
 *
 * @example
 * // Dans Learn.tsx
 * export default function Learn() {
 *   return (
 *     <PageTransition>
 *       <div className="min-h-screen">...</div>
 *     </PageTransition>
 *   )
 * }
 */

import { motion } from 'framer-motion'
import { pageVariants } from '../../lib/motion'

interface PageTransitionProps {
  children:   React.ReactNode
  className?: string
}

export function PageTransition({ children, className }: PageTransitionProps) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={className}
    >
      {children}
    </motion.div>
  )
}
