# {{PROJECT_DISPLAY_NAME}} — Template 0-HITL

Ce projet est basé sur le template **Zero-Human In The Loop (0-HITL)**.

## Personnalisation appliquée

Les placeholders suivants ont été remplacés dans le code source :

| Placeholder | Valeur |
|---|---|
| `{{PROJECT_NAME}}` | Identifiant technique |
| `{{PROJECT_SLUG}}` | Slug URL du projet |
| `{{PROJECT_DOMAIN}}` | Domaine de production |
| `{{PROJECT_DISPLAY_NAME}}` | Nom affiché |
| `{{DEFAULT_EMAIL}}` | Email de contact |

Pour régénérer : `python scripts/replace_placeholders.py --root . --dry-run`

## Configuration requise

Copier `.env.example` en `.env` et renseigner :

```env
# Obligatoire
SECRET_KEY=          # openssl rand -hex 32
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

# Email (production)
SMTP_HOST=smtp.gmail.com
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=

# Admin par défaut (bootstrap au premier démarrage)
ADMIN_EMAIL=
ADMIN_PASSWORD=

# ── Canaux d'inscription ────────────────────────────────────────────────────
AUTH_CHANNEL_WAITLIST=true       # Liste d'attente
AUTH_CHANNEL_DIRECT=false        # Inscription directe
AUTH_CHANNEL_ONBOARDING=false    # Via questionnaire d'onboarding

# ── Monétisation (optionnel) ────────────────────────────────────────────────
MONETIZATION_SHOP=false          # Boutique de produits numériques
MONETIZATION_SUBSCRIPTION=false  # Abonnements Stripe → rôle premium
MONETIZATION_TRIAL_DAYS=0        # Jours d'essai gratuit (0 = aucun)

STRIPE_SECRET_KEY=               # sk_live_… (requis si monétisation activée)
STRIPE_PUBLIC_KEY=               # pk_live_…
STRIPE_WEBHOOK_SECRET=           # whsec_… (depuis Stripe Dashboard → Webhooks)

DOWNLOAD_LINK_EXPIRE_HOURS=48    # Durée de validité des liens de téléchargement
DOWNLOAD_MAX_ATTEMPTS=5          # Nombre max de téléchargements par achat
```

## Démarrage

```bash
# Développement
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Migrations
docker-compose run --rm migrate alembic upgrade head

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## Activer la monétisation

### Boutique (produits numériques — achat unique)

1. Mettre `MONETIZATION_SHOP=true` dans `.env`
2. Renseigner les clés Stripe
3. Créer vos produits dans Stripe Dashboard → Products, récupérer le `price_id`
4. Créer vos produits via l'admin : `POST /api/admin/shop/products`
5. Configurer le webhook Stripe → `https://api.{{PROJECT_DOMAIN}}/api/shop/webhook`

### Abonnements (rôle premium récurrent)

1. Mettre `MONETIZATION_SUBSCRIPTION=true` dans `.env`
2. Créer un produit d'abonnement dans Stripe Dashboard, récupérer son `price_id`
3. Configurer le webhook Stripe (mêmes événements que la boutique)
4. Les utilisateurs accèdent à `/premium` pour s'abonner

## Ajouter un service Agentic IA

1. Créer la définition dans `backend/config/agent_services.yaml`
2. Implémenter la logique dans `backend/app/agents/services/<service>/`
3. Ajouter l'UI dans `frontend/src/agent-services/<service>/`
4. Enregistrer dans `backend/app/routers/agent_services.py`

## Déploiement Production (Traefik)

Le projet est préconfiguré pour Traefik v3 avec HTTPS automatique.

```bash
# Démarrer Traefik (hors du projet, réseau proxy-net partagé)
# Puis démarrer l'application
docker-compose -f docker-compose.prod.yml up -d
```

**Configurer le webhook Stripe en production :**
```
URL : https://api.{{PROJECT_DOMAIN}}/api/shop/webhook
Événements :
  - checkout.session.completed
  - customer.subscription.updated
  - customer.subscription.deleted
  - invoice.payment_succeeded
  - invoice.payment_failed
```

## Documentation complète

Voir [README.md](README.md) et le dossier `docs/`.

---

**Template** : [0-HITL](https://github.com/Nabil-Mabrouk/0-HITL-Template) v1.2.0
