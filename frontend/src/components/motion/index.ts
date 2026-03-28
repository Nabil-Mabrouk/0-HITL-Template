/**
 * Motion components — Animations scroll-triggered basées sur Framer Motion.
 *
 * Tous les comportements d'animation sont contrôlés par `themeConfig.motion`
 * dans src/theme.config.ts. Changer ce paramètre met à jour tout le site.
 *
 * Composants disponibles :
 *
 *   FadeIn         — Fondu + translation verticale au scroll
 *   SlideIn        — Glissement depuis left/right/up/down au scroll
 *   StaggerGroup   — Conteneur qui séquence l'apparition de ses enfants
 *   StaggerItem    — Enfant direct de StaggerGroup
 *   PageTransition — Transition de page (à utiliser avec AnimatePresence dans App.tsx)
 *
 * Utilitaires Framer Motion réexportés depuis lib/motion.ts :
 *   hoverScale, tapScale — Pour whileHover / whileTap sur motion.div
 *
 * @example
 * import { FadeIn, StaggerGroup, StaggerItem, SlideIn } from '../components/motion'
 * import { hoverScale, tapScale } from '../lib/motion'
 */

export { FadeIn }                        from './FadeIn'
export { SlideIn }                       from './SlideIn'
export { StaggerGroup, StaggerItem }     from './StaggerGroup'
export { PageTransition }                from './PageTransition'
