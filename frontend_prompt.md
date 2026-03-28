# Frontend Styling Prompt — 0-HITL Template

Ce fichier est un **prompt prêt à l'emploi** pour demander à un agent LLM (Claude CLI, Gemini CLI, Copilot CLI, etc.) de restyler le frontend de façon cohérente avec le domaine métier de votre application.

---

## Comment utiliser ce prompt

### Claude Code (CLI)
```bash
claude "$(cat frontend_prompt.md)"
```

### Gemini CLI
```bash
gemini -p "$(cat frontend_prompt.md)"
```

### Tout autre LLM en terminal
```bash
<llm-command> "$(cat frontend_prompt.md)"
```

Ou coller directement le contenu dans n'importe quelle interface de chat.

---

## Instructions pour remplir ce prompt

Avant de le lancer, remplissez la section `[DESCRIPTION DE L'APPLICATION]` ci-dessous avec :
- Le secteur / domaine métier de votre application
- Le public cible
- L'ambiance / les émotions que le design doit évoquer
- Des exemples de sites que vous aimez (optionnel)

---

---
## PROMPT À ENVOYER À L'AGENT LLM
*(Tout ce qui suit est destiné à l'agent — ne pas modifier la structure)*

---

### Contexte du projet

Tu travailles sur un projet web fullstack basé sur le template **0-HITL**. Le frontend est une application **React 19 + TypeScript + TailwindCSS v4** avec un système de thème centralisé en un seul fichier.

### Description de l'application

[REMPLACER CE BLOC PAR LA DESCRIPTION DE VOTRE APPLICATION]

Exemple :
> Mon application est une plateforme d'apprentissage de la finance personnelle pour jeunes adultes (18-35 ans).
> Elle doit évoquer la confiance, la clarté et l'optimisme financier.
> J'aime le style de Linear et de Stripe — épuré, sérieux mais accessible.
> Couleur dominante : bleu marine ou vert sauge.

---

### Fichiers clés à modifier

L'ensemble du style visuel est contrôlé par **deux fichiers uniquement** :

#### 1. `frontend/src/theme.config.ts`
Point de contrôle central : preset, couleurs, typographie, géométrie, animations, effets.

```typescript
const themeConfig: ThemeConfig = {

  // PRESET — choisir parmi :
  //   'minimal'   Sombre, épuré, monochromatique (Linear, Vercel, Raycast)
  //   'vibrant'   Clair, énergique, dégradés (Framer, Lemon Squeezy)
  //   'glass'     Sombre, surfaces givrées, profondeur (Apple visionOS)
  //   'brutal'    Zéro radius, bordures épaisses, ombres dures
  //   'editorial' Chaleureux, typographie serif, espace généreux (Substack, Notion)
  preset: 'minimal',

  colors: {
    // Format oklch(lightness% chroma hue)
    // Hue : 0=rouge  30=orange  60=jaune  120=vert  200=teal  264=indigo  310=violet
    primary:   'oklch(62.8% 0.258 264)',
    secondary: 'oklch(58%   0.27  310)',
    accent:    'oklch(74%   0.18   55)',
  },

  fonts: {
    // Heading : impact sur la personnalité visuelle
    //   '"Geist Variable", sans-serif'       Technique / SaaS
    //   '"Cal Sans", "Sora", sans-serif'     Startup / Bold
    //   'Georgia, "Playfair Display", serif' Éditorial
    //   '"DM Sans", sans-serif'              Humaniste
    //   '"Outfit", "Nunito", sans-serif'     Géométrique / Jeune
    heading: '"Geist Variable", system-ui, sans-serif',
    body:    '"Geist Variable", system-ui, sans-serif',
    mono:    '"Geist Mono", "JetBrains Mono", ui-monospace, monospace',
  },

  // GEOMETRY — radius global
  //   'sharp'   0px   Angulaire, technique
  //   'soft'    4px   Minimal, SaaS moderne
  //   'rounded' 8px   Convivial
  //   'pill'    24px  Ludique, consumer app
  geometry: 'rounded',

  // MOTION — intensité des animations
  //   'none'    Aucune animation (accessibilité)
  //   'subtle'  Micro-interactions uniquement
  //   'smooth'  Transitions standard
  //   'playful' Ressorts, staggered effects
  motion: 'smooth',

  effects: {
    // HERO BACKGROUND — effet derrière la section hero
    //   'none'          Couleur unie
    //   'glow-orbs'     Blobs radials flous (dark SaaS classique)
    //   'mesh-gradient' Dégradé animé
    //   'grid-dots'     Grille de points, look technique
    //   'noise'         Texture grain
    heroBackground: 'glow-orbs',

    // CARD STYLE
    //   'flat' | 'elevated' | 'bordered' | 'glass'
    cardStyle: 'elevated',

    // BUTTON STYLE
    //   'filled' | 'outlined' | 'gradient' | 'brutal'
    buttonStyle: 'filled',
  },
}
```

#### 2. `frontend/src/index.css`
Définit les variables CSS globales (couleurs shadcn/ui, dark mode, font-family mappings).
Les variables `--primary`, `--secondary`, `--accent` dans `:root` et `.dark` peuvent être ajustées si les couleurs du preset ne suffisent pas.

---

### Ta mission

En te basant sur la description de l'application fournie ci-dessus :

1. **Choisir le preset** le plus adapté au secteur et à l'ambiance souhaitée.

2. **Définir la palette de couleurs** en utilisant le format `oklch()` :
   - `primary` : couleur d'action principale (boutons, liens, accents)
   - `secondary` : couleur complémentaire (dégradés, survols)
   - `accent` : couleur de mise en valeur (badges, notifications, underlines)
   - Justifier chaque choix de couleur en termes d'émotion et de secteur.

3. **Choisir la typographie** :
   - Police de heading adaptée à la personnalité de l'app
   - Si une police Google Fonts ou autre est choisie, indiquer la commande `npm install` correspondante et l'import CSS à ajouter dans `index.css`

4. **Ajuster geometry et motion** selon le public cible :
   - B2B / Entreprise → `sharp` ou `soft` + `subtle`
   - Consumer / Grand public → `rounded` ou `pill` + `smooth` ou `playful`

5. **Choisir l'effet hero** cohérent avec l'ambiance :
   - Finance, santé, confiance → `glow-orbs` discrets ou `mesh-gradient` doux
   - Technique, dev tools → `grid-dots`
   - Créatif, agence → `mesh-gradient` ou `noise`

6. **Modifier uniquement** `frontend/src/theme.config.ts` (et `index.css` si nécessaire).
   Ne pas toucher aux composants ni aux pages — le système de thème s'en charge.

7. **Expliquer brièvement** les choix effectués (2-3 phrases par décision majeure).

### Contraintes

- Rester dans les options disponibles définies dans `ThemeConfig`
- Si une police externe est nécessaire, elle doit être disponible via npm (`@fontsource-variable/...` de préférence)
- Ne pas modifier les fichiers de composants React (`.tsx`)
- Ne pas modifier `tailwind.config.ts` ni `vite.config.ts`
- Le résultat doit être cohérent entre dark mode et light mode

---
*Fin du prompt*
