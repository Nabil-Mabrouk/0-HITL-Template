# Dashboard Admin et Analytics

## Introduction

Une plateforme comme **0-HITL** nécessite une interface de pilotage robuste pour les administrateurs. Le Dashboard Admin n'est pas seulement un outil de gestion de contenu ; c'est un centre de commandement qui permet de surveiller l'activité des utilisateurs et de prendre des décisions basées sur les données.

## Architecture du Dashboard

Le dashboard est organisé en six modules accessibles via un système d'onglets :
1.  **Utilisateurs :** Gestion des comptes, rôles et suspensions.
2.  **Waitlist :** Pilotage des invitations pour l'accès anticipé.
3.  **Analytics :** Visualisation des flux de trafic et de l'audience.
4.  **Contenu :** Administration de l'université virtuelle (tutoriaux et leçons).
5.  **Sécurité :** Surveillance des tentatives d'intrusion en temps réel.
6.  **Boutique :** Gestion des produits, ventes et abonnements (si monétisation activée).

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

## Surveillance de la Sécurité

L'onglet **Sécurité** du Dashboard expose les données collectées par le `SecurityMiddleware`, qui surveille en continu chaque requête entrante.

### Types d'événements détectés

| Type | Exemples | Sévérité |
|---|---|---|
| `path_scan` | `/.git/`, `/.env`, `/wp-config.php` | medium → critical |
| `scanner_detected` | UA de sqlmap, nikto, nmap, nuclei | high |
| `injection_attempt` | SQL injection, XSS, template injection | critical |

### Interface admin

Le tableau de bord affiche :
- **Cartes de synthèse** : total des événements, dernières 24h, critiques, élevés
- **Top 10 des IPs agressives** : identifier les attaquants récurrents
- **Journal filtrable** : par sévérité, type, IP, période

```tsx
// Appels API utilisés par l'onglet Sécurité
GET /api/admin/security/summary?days=7
GET /api/admin/security/events?severity=critical&page=1&per_page=50
DELETE /api/admin/security/events/old?days=30   // purge périodique
```

**Note importante :** Le middleware ne bloque jamais les requêtes — il journalise uniquement. Cette approche est intentionnelle : elle évite les faux positifs pouvant bloquer des utilisateurs légitimes tout en donnant une visibilité complète sur les menaces. Le blocage peut être ajouté au niveau Traefik (via `fail2ban` ou des règles IP).

## Administration de la Boutique

Lorsque `MONETIZATION_SHOP=true` ou `MONETIZATION_SUBSCRIPTION=true`, l'onglet **Boutique** devient disponible.

### Gestion des Produits

Les administrateurs peuvent créer et gérer les produits directement depuis l'API (ou via l'onglet admin) :

```bash
# Créer un produit
POST /api/admin/shop/products
{
  "name":            "Guide Complet FastAPI",
  "slug":            "guide-fastapi",
  "description":     "PDF de 200 pages...",
  "price_cents":     2900,            # 29 €
  "currency":        "eur",
  "stripe_price_id": "price_xxx",     # depuis Stripe Dashboard
  "file_path":       "/data/guides/fastapi.pdf"
}
```

### Tableau de bord des ventes

L'endpoint `/api/admin/shop/stats` fournit :

```json
{
  "sales": {
    "total_cents":     150000,
    "last_30d_cents":  45000,
    "total_purchases": 52
  },
  "subscriptions": {
    "active":    120,
    "trialing":  15,
    "cancelled": 8,
    "past_due":  2
  }
}
```

Ces données permettent de calculer le **MRR** (Monthly Recurring Revenue) et de suivre la croissance des revenus.

---

*Le pilotage par la donnée étant assuré, nous allons maintenant voir comment rendre notre plateforme visible sur le web grâce à une stratégie SEO avancée dans le chapitre suivant.*
