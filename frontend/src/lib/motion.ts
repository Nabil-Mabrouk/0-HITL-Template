/**
 * motion.ts — Pont entre theme.config.ts et Framer Motion.
 *
 * Toutes les animations du projet dérivent de `themeConfig.motion`.
 * Changer ce paramètre dans theme.config.ts met à jour l'ensemble du système
 * d'animation : durées, distances, ressorts, stagger delays.
 *
 * Niveaux disponibles (définis dans theme.config.ts) :
 *   'none'    → Aucune animation (accessibilité, performance)
 *   'subtle'  → Micro-interactions, opacité seule
 *   'smooth'  → Translations + opacité, courbe naturelle
 *   'playful' → Ressorts, rebond, stagger expressif
 */

import themeConfig from '../theme.config'

type MotionLevel = typeof themeConfig.motion

// ── Config interne par niveau ─────────────────────────────────────────────────

const DURATIONS: Record<MotionLevel, number> = {
  none:    0,
  subtle:  0.15,
  smooth:  0.4,
  playful: 0.45,
}

const Y_OFFSETS: Record<MotionLevel, number> = {
  none:    0,
  subtle:  8,
  smooth:  24,
  playful: 36,
}

const SCALE_INITIAL: Record<MotionLevel, number> = {
  none:    1,
  subtle:  1,
  smooth:  1,
  playful: 0.94,
}

export const STAGGER_DELAY: Record<MotionLevel, number> = {
  none:    0,
  subtle:  0.04,
  smooth:  0.08,
  playful: 0.12,
}

// ── Transition par niveau ─────────────────────────────────────────────────────

const BASE_TRANSITIONS: Record<MotionLevel, object> = {
  none: {
    duration: 0,
  },
  subtle: {
    duration: DURATIONS.subtle,
    ease: 'easeOut',
  },
  smooth: {
    duration: DURATIONS.smooth,
    ease: [0.25, 0.46, 0.45, 0.94] as number[],
  },
  playful: {
    type: 'spring',
    stiffness: 300,
    damping: 24,
    mass: 0.8,
  },
}

// ── Exports de base ───────────────────────────────────────────────────────────

/** Niveau de motion actif (depuis theme.config.ts) */
export const motionLevel: MotionLevel = themeConfig.motion

/** True si les animations sont activées */
export const isAnimated: boolean = motionLevel !== 'none'

/** Transition Framer Motion correspondant au niveau actif */
export const transition = BASE_TRANSITIONS[motionLevel]

// ── Variants réutilisables ────────────────────────────────────────────────────

/**
 * fadeInVariants — Apparition avec fondu + descente légère.
 * Usage : <motion.div variants={fadeInVariants} initial="hidden" animate="visible">
 */
export const fadeInVariants = {
  hidden: {
    opacity: isAnimated ? 0 : 1,
    y:       Y_OFFSETS[motionLevel],
    scale:   SCALE_INITIAL[motionLevel],
  },
  visible: {
    opacity: 1,
    y:       0,
    scale:   1,
    transition,
  },
}

/**
 * slideInVariants — Glissement depuis une direction.
 * Usage : const v = slideInVariants('left')
 */
export function slideInVariants(from: 'left' | 'right' | 'up' | 'down' = 'left') {
  const dist  = isAnimated ? (motionLevel === 'subtle' ? 16 : 48) : 0
  const xMap  = { left: -dist, right: dist, up: 0,    down: 0    }
  const yMap  = { left: 0,     right: 0,    up: -dist, down: dist }
  return {
    hidden:  { opacity: isAnimated ? 0 : 1, x: xMap[from], y: yMap[from] },
    visible: { opacity: 1, x: 0, y: 0, transition },
  }
}

/**
 * staggerContainerVariants — Conteneur qui séquence ses enfants.
 * Les enfants doivent utiliser fadeInVariants ou un variant "hidden/visible".
 */
export const staggerContainerVariants = {
  hidden:  {},
  visible: {
    transition: {
      staggerChildren: STAGGER_DELAY[motionLevel],
      delayChildren:   0.05,
    },
  },
}

/**
 * pageVariants — Transition entre routes (utilisé avec AnimatePresence).
 * Plus courte que fadeIn pour ne pas alourdir la navigation.
 */
export const pageVariants = {
  initial: { opacity: isAnimated ? 0 : 1, y: isAnimated ? 8 : 0 },
  animate: {
    opacity: 1,
    y:       0,
    transition: { duration: 0.25, ease: 'easeOut' },
  },
  exit: {
    opacity:    isAnimated ? 0 : 1,
    transition: { duration: 0.15, ease: 'easeIn' },
  },
}

/**
 * hoverVariants — Survol interactif pour les cartes et boutons.
 * Usage : <motion.div whileHover={hoverScale} whileTap={tapScale}>
 */
export const hoverScale = isAnimated
  ? { scale: motionLevel === 'playful' ? 1.04 : 1.02, transition: { duration: 0.15 } }
  : {}

export const tapScale = isAnimated
  ? { scale: 0.97, transition: { duration: 0.1 } }
  : {}
