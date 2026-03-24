# L'Université Virtuelle : Catalogue et Contenu

## Introduction

Le cœur de la plateforme **0-HITL** est son université virtuelle. Elle permet de diffuser du savoir technique de manière structurée via des tutoriaux et des leçons interactives. Dans ce chapitre, nous verrons comment nous avons construit un catalogue dynamique et un moteur de rendu de contenu riche.

## Le Catalogue de Tutoriaux

Le catalogue est la porte d'entrée pour l'apprenant. Il doit être à la fois clair et intelligent pour ne proposer que le contenu pertinent.

### Filtrage par Langue et Rôle
Grâce à l'intégration de `i18next` côté frontend et d'un paramètre `lang` côté API, l'utilisateur ne voit que les cours disponibles dans sa langue sélectionnée. De plus, un système de badges indique visuellement si un cours est **Gratuit** ou **Premium**.

```tsx
// Learn.tsx
useEffect(() => {
  const lang = i18n.language.split("-")[0];
  fetch(`${API}/api/content/tutorials?lang=${lang}`)
    .then(data => setTutorials(data));
}, [i18n.language]);
```

## Le Moteur de Rendu Markdown

Pour un contenu technique, le format **Markdown** est idéal. Il permet aux auteurs d'écrire rapidement tout en supportant du code, des tableaux et des liens. Nous avons créé un composant `MarkdownRenderer` basé sur `react-markdown`.

### Fonctionnalités avancées du moteur :
1.  **GFM (GitHub Flavored Markdown) :** Support des tableaux, des listes de tâches et des liens automatiques.
2.  **Syntax Highlighting :** Coloration syntaxique du code via `rehype-highlight` et le thème GitHub Dark.
3.  **Embeds Multimédia :** Nous avons étendu le Markdown pour supporter des balises personnalisées comme `[video:URL]` ou `[audio:URL]`.
4.  **Intégration YouTube :** Détection automatique des liens YouTube pour les transformer en lecteurs vidéo `iframe`.

```tsx
// Exemple de pré-traitement du contenu
const processed = content.replace(
  /\[video:(.*?)\]/g,
  (_, url) => `<video controls src="${url}"></video>`
);
```

## Contrôle d'Accès au Contenu

La sécurité est gérée à deux niveaux. Le frontend masque les liens vers le contenu Premium pour les utilisateurs non autorisés, tandis que le backend vérifie systématiquement les permissions via un middleware avant de délivrer le contenu d'une leçon.

---

*L'université étant fonctionnelle, nous allons maintenant nous intéresser à l'expérience d'arrivée des nouveaux utilisateurs : l'onboarding dynamique dans le chapitre suivant.*
