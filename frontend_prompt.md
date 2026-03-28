# Frontend Styling Prompt — 0-HITL Template

Ce fichier est un **prompt prêt à l'emploi** pour demander à un agent LLM (Claude CLI,
Gemini CLI, Copilot CLI, etc.) de restyler et restructurer le frontend de façon cohérente
avec le domaine métier de votre application.

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

### Copilot CLI / tout autre LLM en terminal
```bash
<llm-command> "$(cat frontend_prompt.md)"
```

Ou coller directement le contenu dans n'importe quelle interface de chat.

---

## Avant de lancer

**Remplissez la section `[DESCRIPTION DE VOTRE APPLICATION]` ci-dessous.**

Plus votre description est précise, plus le résultat sera adapté. Pensez à inclure :
- Le domaine métier / secteur
- Le public cible (âge, profil, niveau technique)
- L'ambiance et les émotions que le design doit évoquer
- Les sections qui ont du sens pour votre produit (témoignages ? démo ? pricing ?)
- Des références visuelles (sites que vous aimez)
- La langue principale du site (FR / EN / autre)

---

---
## PROMPT À ENVOYER À L'AGENT LLM
*(Tout ce qui suit est destiné à l'agent — copier-coller tel quel)*

---

### Rôle

Tu es un expert en design de produits web et en développement frontend React. Ta mission
est de transformer le frontend d'un template générique en une interface parfaitement
adaptée au domaine métier décrit ci-dessous — visuellement cohérente, structurellement
pertinente et émotionnellement juste.

---

### Description de l'application

[REMPLACER CE BLOC PAR LA DESCRIPTION DE VOTRE APPLICATION]

Exemple :
> Application de suivi de santé mentale pour professionnels de santé.
> Public : thérapeutes et psychiatres, 30-55 ans, contexte B2B.
> Ambiance : rassurante, professionnelle, sobre. Pas de couleurs criardes.
> Sections souhaitées : hero avec accroche forte, 3 fonctionnalités clés,
> témoignages de praticiens, pricing simple, CTA d'inscription.
> Référence visuelle : Notion, Linear. Couleur dominante : bleu ardoise ou vert sauge.
> Langue principale : Français.

---

### Architecture du projet (à lire avant de commencer)

**Stack** : React 19 · TypeScript · TailwindCSS v4 · Vite · react-i18next

#### Fichiers que tu PEUX et DOIS modifier

| Fichier | Rôle | Priorité |
|---|---|:---:|
| `frontend/src/pages/Landing.tsx` | Page d'accueil — à **reconstruire** complètement | 🔴 Obligatoire |
| `frontend/src/theme.config.ts` | Identité visuelle globale (preset, couleurs, fonts, animations) | 🔴 Obligatoire |
| `frontend/src/components/Navbar.tsx` | Navigation — adapter les liens et le logo si nécessaire | 🟡 Si besoin |
| `frontend/src/pages/Learn.tsx` | Page contenu/cours — adapter le layout si le domaine le justifie | 🟡 Si besoin |
| `frontend/src/pages/Shop.tsx` | Boutique — adapter titre et description | 🟡 Si besoin |
| `frontend/src/pages/Premium.tsx` | Page abonnement — adapter le pitch | 🟡 Si besoin |
| `frontend/public/locales/fr/common.json` | Traductions françaises (nav, landing, waitlist…) | 🔴 Obligatoire |
| `frontend/public/locales/en/common.json` | Traductions anglaises | 🔴 Obligatoire |
| `frontend/src/index.css` | Variables CSS globales (si les presets ne suffisent pas) | 🟡 Si besoin |

#### Fichiers à NE PAS toucher

- `frontend/src/pages/Login.tsx` / `Register.tsx` / `ForgotPassword.tsx` / `ResetPassword.tsx` / `VerifyEmail.tsx` / `Onboarding.tsx`
- `frontend/src/pages/admin/` et `frontend/src/pages/Profile.tsx`
- `frontend/src/auth/AuthRouter.tsx` et `frontend/src/context/AuthContext.tsx`
- `frontend/src/App.tsx` (routing)
- `frontend/vite.config.ts`, `frontend/tsconfig*.json`, `backend/`

---

### Phase 1 — Identité visuelle (`theme.config.ts`)

Commence par définir l'identité visuelle globale dans `frontend/src/theme.config.ts`.
Ce fichier contrôle l'ensemble du système de design via ces options :

#### Presets disponibles (point de départ, pas une contrainte)
```
'minimal'   — Sombre, épuré, monochromatique.    Inspiration : Linear, Vercel, Raycast
'vibrant'   — Clair, dégradés, haute énergie.    Inspiration : Framer, Lemon Squeezy
'glass'     — Sombre, surfaces givrées.          Inspiration : Apple visionOS, dashboards gaming
'brutal'    — Zéro radius, bordures épaisses.    Inspiration : design brutaliste, agences créatives
'editorial' — Tons chauds, sérifs, whitespace.   Inspiration : Substack, Notion, magazines
```

#### Options complètes
```typescript
const themeConfig: ThemeConfig = {
  preset: 'minimal',   // choisir le plus proche du domaine

  colors: {
    // Format oklch(lightness% chroma hue) — très expressif
    // Hue : 0=rouge  30=orange  60=jaune  120=vert  200=teal  264=indigo  310=violet
    primary:   'oklch(62.8% 0.258 264)',  // couleur d'action principale
    secondary: 'oklch(58%   0.27  310)',  // couleur complémentaire
    accent:    'oklch(74%   0.18   55)',  // mise en valeur (badges, underlines)
  },

  fonts: {
    // Exemples par personnalité :
    //   Technique / SaaS     → '"Geist Variable", sans-serif'
    //   Startup / Dynamique  → '"Cal Sans", "Sora", sans-serif'
    //   Éditorial / Sérieux  → 'Georgia, "Playfair Display", serif'
    //   Humaniste / Doux     → '"DM Sans", sans-serif'
    //   Géométrique / Jeune  → '"Outfit", "Nunito", sans-serif'
    heading: '"Geist Variable", system-ui, sans-serif',
    body:    '"Geist Variable", system-ui, sans-serif',
    mono:    '"Geist Mono", ui-monospace, monospace',
  },

  geometry: 'rounded',  // 'sharp' | 'soft' | 'rounded' | 'pill'
  motion:   'smooth',   // 'none' | 'subtle' | 'smooth' | 'playful'

  effects: {
    heroBackground: 'glow-orbs',  // 'none' | 'glow-orbs' | 'mesh-gradient' | 'grid-dots' | 'noise'
    cardStyle:      'elevated',   // 'flat' | 'elevated' | 'bordered' | 'glass'
    buttonStyle:    'filled',     // 'filled' | 'outlined' | 'gradient' | 'brutal'
  },
}
```

Si une police externe est nécessaire, ajouter l'import npm dans `index.css` et indiquer
la commande `npm install @fontsource-variable/<nom>`.

---

### Phase 2 — Reconstruire `Landing.tsx`

La `Landing.tsx` actuelle est un placeholder minimal (badge + titre + waitlist form).
**Elle doit être entièrement reconstruite** pour refléter le produit réel.

#### Composants disponibles à importer
```tsx
// Effets de fond (positionner dans un container `relative`)
import { GlowOrbs, MeshGradient, GridDots, NoiseOverlay, AnimatedBorder }
  from "../components/effects"

// Composants fonctionnels
import { WaitlistForm } from "../components/WaitlistForm"  // formulaire d'inscription waitlist
import SEO from "../components/SEO"                         // balises meta/og
import { Button } from "../components/ui/button"
import { Card }   from "../components/ui/card"
import { Badge }  from "../components/ui/badge"

// Routing
import { useNavigate } from "react-router-dom"

// Traductions
import { useTranslation } from "react-i18next"
```

#### Sections courantes selon le domaine — guide de sélection

Choisir les sections adaptées au domaine décrit, pas forcément toutes :

| Section | Quand l'inclure |
|---|---|
| **Hero** | Toujours. Accroche principale + CTA primaire |
| **Social proof / logos** | Si le produit cible des entreprises ou a des partenaires |
| **Fonctionnalités** | Si le produit a des features distinctives à expliquer (2-6 max) |
| **Comment ça marche** | Si le flux utilisateur n'est pas évident (3 étapes max) |
| **Témoignages** | Si crédibilité et confiance sont clés (santé, finance, éducation) |
| **Pricing** | Si le modèle est simple et que l'afficher n'est pas prématuré |
| **FAQ** | Si des objections fréquentes méritent d'être adressées |
| **CTA final** | Toujours. Reprend l'action principale du hero |
| **Footer** | Toujours. Liens légaux, copyright, liens sociaux |

#### Règles de construction de `Landing.tsx`

1. **Utiliser les classes Tailwind v4 uniquement** — pas de style inline sauf cas exceptionnel
2. **Utiliser les variables CSS du thème** : `text-primary`, `bg-primary`, `border-primary`,
   `text-secondary`, `text-accent`, `bg-background`, `text-foreground`, `border-border`, etc.
3. **Respecter la responsive** : mobile first, breakpoints `md:` et `lg:`
4. **Conserver `<SEO>` en tête de composant** avec title, description et url adaptés au projet
5. **Les textes doivent passer par i18n** : utiliser `useTranslation` + clés dans les fichiers
   de locale (voir Phase 3). Pour les textes longs ou spécifiques, écrire directement en dur
   est acceptable dans un premier temps
6. **Les effets de fond** (`GlowOrbs`, etc.) s'utilisent dans un container `relative overflow-hidden` :
   ```tsx
   <section className="relative overflow-hidden">
     <GlowOrbs />   {/* positionné en absolu en arrière-plan */}
     <div className="relative z-10">
       {/* contenu */}
     </div>
   </section>
   ```

---

### Phase 3 — Mettre à jour les traductions i18n

Mettre à jour les deux fichiers de locale pour refléter le nouveau contenu :

**`frontend/public/locales/fr/common.json`** et **`frontend/public/locales/en/common.json`**

Ajouter les clés nécessaires dans la section `"landing"` et créer de nouvelles sections
si besoin (ex: `"features"`, `"pricing"`, `"testimonials"`).

Structure actuelle à adapter :
```json
{
  "landing": {
    "hero_title":    "...",
    "hero_subtitle": "...",
    "cta_primary":   "...",
    "cta_secondary": "..."
  }
}
```

---

### Phase 4 — Adapter la Navbar si nécessaire

Dans `frontend/src/components/Navbar.tsx`, le texte du logo (actuellement `"0-HITL"`)
doit être remplacé par le nom du projet. Adapter aussi les liens si certaines pages
n'existent pas encore dans ce projet (ex: masquer `/learn` si le produit n'a pas de
section cours).

---

### Livrable attendu

Pour chaque fichier modifié, fournir le code complet du fichier (pas de diff partiel).
Justifier brièvement (1-2 phrases) les choix de design majeurs :
- Pourquoi ce preset
- Pourquoi cette palette de couleurs
- Pourquoi ces sections sur la landing

---

### Exemple d'enchaînement de sections pour différents domaines

**SaaS B2B** (outil métier, audience technique) :
```
Hero → Logos clients → 3-4 Features → How it works → Témoignages → Pricing → CTA → Footer
```

**EdTech / Learning** (plateforme de cours) :
```
Hero → Statistiques sociales → Ce que tu apprendras → Témoignages étudiants → Pricing/Accès → FAQ → CTA → Footer
```

**Marketplace / Community** (mise en relation) :
```
Hero → How it works (3 étapes) → Profiles mis en avant → Témoignages → CTA double (offreur + demandeur) → Footer
```

**Health / Wellness** (santé, bien-être) :
```
Hero rassurant → Problème adressé → Approche / Méthode → Preuves (études, certifications) → Témoignages → CTA doux → Footer
```

**Fintech / Finance** (investissement, épargne) :
```
Hero avec chiffre clé → Sécurité & conformité → Features → Témoignages → Pricing transparent → FAQ → CTA → Footer
```

**Creative / Agency** (portfolio, agence) :
```
Hero fort visuellement → Travaux récents (grid) → Services → Process → Équipe → Contact → Footer
```

---
*Fin du prompt*
