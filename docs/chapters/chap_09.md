# Dashboard Admin et Analytics

## Introduction

Une plateforme comme **0-HITL** nécessite une interface de pilotage robuste pour les administrateurs. Le Dashboard Admin n'est pas seulement un outil de gestion de contenu ; c'est un centre de commandement qui permet de surveiller l'activité des utilisateurs et de prendre des décisions basées sur les données.

## Architecture du Dashboard

Le dashboard est organisé en quatre modules principaux accessibles via un système d'onglets :
1.  **Utilisateurs :** Gestion des comptes, rôles et suspensions.
2.  **Waitlist :** Pilotage des invitations pour l'accès anticipé.
3.  **Analytics :** Visualisation des flux de trafic et de l'audience.
4.  **Contenu :** Administration de l'université virtuelle (tutoriaux et leçons).

## Gestion de l'Audience

### La Waitlist (Accès Anticipé)
Pour gérer une croissance progressive, 0-HITL utilise une liste d'attente. Les administrateurs peuvent envoyer ou renvoyer des invitations d'un simple clic, générant automatiquement des jetons d'invitation uniques stockés en base de données.

### Modération et Rôles
L'interface permet de modifier dynamiquement le rôle d'un utilisateur (ex: passer un compte de `user` à `premium`) ou de suspendre un accès en cas de comportement suspect.

## Visualisation des Données (Analytics)

L'analytique est ce qui rend le dashboard "vivant". Nous utilisons deux composants de visualisation avancée :

### 1. La Carte Mondiale (World Map)
Grâce à `react-simple-maps` et aux données GeoIP collectées par notre middleware backend, nous affichons la provenance géographique des visiteurs. Cela permet d'identifier les marchés ou les régions les plus actives.

### 2. Timeline d'Activité
En utilisant `recharts`, nous générons des graphiques temporels montrant le nombre de visites par jour. Ces données sont filtrables par rôle (Anonymes, Membres, Admins) pour une analyse fine de l'usage.

```tsx
// Exemple simplifié de l'appel Analytics
const params = new URLSearchParams({ days: "30" });
const res = await fetch(`/api/admin/analytics/world?${params}`);
```

## Bibliothèque de Médias

Le dashboard intègre également un gestionnaire de fichiers. Les administrateurs peuvent uploader des images, des vidéos ou des documents PDF qui seront ensuite facilement insérables dans les leçons de l'université virtuelle via un système de "copy-paste" de snippets Markdown.

---

*Le pilotage par la donnée étant assuré, nous allons maintenant voir comment rendre notre plateforme visible sur le web grâce à une stratégie SEO avancée dans le chapitre suivant.*
