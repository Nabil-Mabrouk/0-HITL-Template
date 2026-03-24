
# Onboarding Dynamique et Profilage

## Introduction

L'une des fonctionnalités les plus innovantes de **0-HITL** est son système d'onboarding. Contrairement à une inscription classique, nous utilisons un tunnel interactif pour comprendre les besoins de l'utilisateur et lui attribuer un profil technique précis.

## L'Expérience Utilisateur (Frontend)

L'onboarding est découpé en plusieurs phases gérées par un automate à états dans React :
1.  **Phase Questions :** Affichage séquentiel des questions chargées dynamiquement depuis l'API.
2.  **Phase Résultat :** Affichage du score et du profil calculé (ex: *AI Architect*).
3.  **Phase Inscription :** Formulaire de création de compte pré-rempli avec le contexte du profil.

### Gestion de la Progression
Nous utilisons un indicateur visuel de progression pour encourager l'utilisateur à terminer le questionnaire. Chaque réponse est stockée localement dans un état `answers` avant d'être envoyée pour évaluation finale.

## Le Tunnel Multi-Mode

Le composant `Onboarding.tsx` est conçu pour être réutilisable. Il gère deux cas d'usage majeurs :
*   **Mode Inscription :** Pour les nouveaux visiteurs arrivant sur la plateforme.
*   **Mode Mise à jour :** Pour les utilisateurs connectés qui souhaitent redéfinir leur profil d'usage.

Cette polyvalence est possible grâce à une vérification initiale de l'état d'authentification :
```tsx
const isUpdate = (searchParams.get("update") === "true") || (user !== null);
```

## Évaluation et Scoring (Backend)

Lorsqu'un utilisateur répond à la dernière question, le frontend appelle l'endpoint `/api/onboarding/evaluate`.

### Le Contrat d'Évaluation
Le backend reçoit un dictionnaire de réponses et le compare aux règles du "Flow" JSON. Il retourne deux éléments clés :
1.  **Scoring Result :** Le profil technique calculé.
2.  **Result Screen :** Une configuration visuelle (titre, description, CTA) personnalisée selon le score obtenu.

## Persistance du Profil

Une fois le compte créé ou mis à jour, les réponses brutes et le profil calculé sont sauvegardés dans la table `UserProfile`. Cela permet de :
*   Personnaliser l'interface du `Profile` utilisateur.
*   Adapter le catalogue de cours dans le futur.
*   Fournir des analytics précis sur la typographie de l'audience.

---

*L'utilisateur étant maintenant profilé et connecté, nous allons voir comment les administrateurs pilotent la plateforme grâce au Dashboard et aux Analytics dans le chapitre suivant.*
