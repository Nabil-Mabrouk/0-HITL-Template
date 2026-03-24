---
title: "SEO et Optimisation pour la Visibilité"
---

## Introduction

Une application performante ne sert à rien si elle n'est pas trouvable par les moteurs de recherche. Dans ce chapitre, nous allons voir comment optimiser le projet **0-HITL** pour le référencement naturel (SEO), tout en conservant les avantages d'une application Single Page (SPA).

## Gestion Dynamique des Meta Tags

Contrairement aux frameworks comme Next.js qui gèrent cela nativement côté serveur, une application React nécessite une bibliothèque tierce pour modifier les balises `<head>`. Nous utilisons `react-helmet-async`.

### Le Composant SEO Réutilisable
Nous avons centralisé la gestion des balises dans un composant unique. Il gère :
*   Le titre de la page (formaté avec le nom du site).
*   La description pour Google.
*   Les balises **Open Graph** pour un partage élégant sur Facebook/LinkedIn.
*   Les **Twitter Cards** pour les aperçus sur X.
*   La balise `canonical` pour éviter le contenu dupliqué.

```tsx
<SEO 
  title="Apprendre l'automatisation" 
  description="Découvrez nos tutoriaux HITL"
  url="/learn"
/>
```

## Sitemap et Robots.txt Dynamiques

Pour que les robots d'indexation (Googlebot) découvrent tout notre contenu, nous avons besoin d'un fichier `sitemap.xml`. Puisque nos tutoriaux sont stockés en base de données, ce fichier doit être généré dynamiquement par le backend.

### Génération côté Backend (FastAPI)
L'endpoint `/sitemap.xml` parcourt la table `Tutorial` et génère un flux XML listant toutes les URLs publiques avec leur date de dernière modification.

```python
@router.get("/sitemap.xml")
async def sitemap(db: Session = Depends(get_db)):
    tutorials = db.query(Tutorial).filter(Tutorial.is_published == True).all()
    # Génération du XML...
```

## Données Structurées (JSON-LD)

Pour apparaître sous forme de "Rich Snippets" (extraits enrichis) dans les résultats de recherche, nous intégrons des données structurées au format **Schema.org**. 

Pour la page d'un tutorial, nous utilisons le type `Course`, qui permet à Google d'afficher le nombre de leçons et la durée du cours directement dans ses résultats.

## Indexation Sélective (`noindex`)

Toutes les pages ne doivent pas être indexées. Les pages de profil utilisateur ou le dashboard d'administration contiennent des informations privées ou sensibles. Nous utilisons la propriété `noindex={true}` de notre composant SEO pour envoyer l'instruction aux moteurs de recherche de ne pas référencer ces pages.

---

*Notre plateforme est désormais visible et optimisée. Dans le prochain chapitre, nous allons voir comment préparer l'ensemble pour un déploiement massif en production grâce à Docker.*
