# Zero-Human In The Loop — Agentic AI Platform Template

Un template fullstack complet pour lancer une plateforme web avec gestion des utilisateurs, contenu pédagogique, services d'IA agentique et **monétisation intégrée**.

## Fonctionnalités

### Backend (FastAPI)
- Authentification utilisateur (JWT, refresh tokens, OAuth2)
- Système de rôles hiérarchique : `anonymous → waitlist → user → premium → admin`
- Base de données PostgreSQL avec migrations Alembic
- API REST complète avec rate limiting (SlowAPI)
- Services agentic IA modulaires (orchestrateur multi-agents, mémoire, garde-fous)
- Email transactionnel (vérification, reset MDP, invitations, confirmations d'achat)
- Tracking géographique anonymisé (GeoIP, RGPD)
- Analytics (cartes, timelines, stats)
- Dashboard admin (utilisateurs, contenu, analytics, sécurité, boutique)
- **Monétisation** : vente de produits numériques + abonnements Stripe (activables via `.env`)
- **Sécurité** : middleware de détection d'intrusion, journalisation des événements, dashboard

### Frontend (React 19 / TypeScript)
- Landing page responsive (dark mode)
- Authentification complète (login, register, verify, reset)
- Système de canaux d'auth configurable (waitlist / direct / onboarding)
- Onboarding dynamique avec profilage utilisateur
- Université virtuelle (tutoriaux, leçons Markdown, accès premium)
- Page profil (infos, mot de passe, achats, lien de téléchargement)
- **Boutique** (`/shop`) : catalogue produits, checkout Stripe, page succès
- **Premium** (`/premium`) : plans d'abonnement, portail Stripe, statut
- Dashboard admin : onglets utilisateurs, waitlist, analytics, sécurité, boutique
- SEO avancé (sitemap dynamique, robots.txt, llms.txt, react-helmet-async)
- Internationalisation i18n (FR/EN)

### Services Agentic IA
- Architecture modulaire (services YAML + agents Python)
- Orchestrateur multi-étapes avec partage de contexte
- Mémoire à court/long terme
- Garde-fous (validation entrées/sorties)
- Historique complet des exécutions
- Dashboard unifié

### Infrastructure
- Docker Compose (dev avec hot-reload, prod multi-stage optimisé)
- Traefik v3 (HTTPS automatique Let's Encrypt, rate-limit, access logs JSON)
- Scheduler de maintenance DB (nettoyage automatique)
- Script de personnalisation des placeholders (`{{PROJECT_NAME}}`, etc.)

## Structure du Projet

```
.
├── backend/
│   ├── app/
│   │   ├── agents/           # Framework agentic IA
│   │   │   ├── core/         # Orchestrateur, mémoire, garde-fous
│   │   │   ├── services/     # Services modulaires
│   │   │   └── tools/        # Outils disponibles
│   │   ├── auth/             # JWT, sécurité, dépendances
│   │   ├── email/            # Service SMTP + templates Jinja2
│   │   ├── middleware/        # SecurityMiddleware, TrackingMiddleware
│   │   ├── routers/          # Endpoints API
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── admin.py
│   │   │   ├── content.py / admin_content.py
│   │   │   ├── shop.py           # Boutique produits numériques
│   │   │   ├── shop_webhook.py   # Webhook Stripe (signature vérifiée)
│   │   │   ├── subscription.py   # Abonnements Stripe
│   │   │   ├── admin_shop.py     # Admin boutique + MRR
│   │   │   └── security.py       # Admin événements sécurité
│   │   ├── models.py         # Tous les modèles SQLAlchemy
│   │   ├── config.py         # Settings Pydantic (chargés depuis .env)
│   │   └── main.py           # App FastAPI, middleware, routers
│   ├── alembic/              # Migrations DB
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Shop.tsx          # Boutique
│   │   │   ├── ShopSuccess.tsx   # Confirmation achat
│   │   │   ├── Premium.tsx       # Abonnements
│   │   │   ├── Profile.tsx       # Profil + Mes achats
│   │   │   └── admin/Dashboard.tsx
│   │   ├── components/       # SEO, WaitlistForm, MarkdownRenderer…
│   │   ├── auth/             # AuthRouter (canaux d'auth)
│   │   └── context/          # AuthContext
│   └── public/               # robots.txt, llms.txt
├── docker-compose.yml
├── docker-compose.dev.yml
├── docker-compose.prod.yml
├── .env.example
└── scripts/
    └── replace_placeholders.py
```

## Installation Rapide

### 1. Cloner et configurer

```bash
git clone https://github.com/Nabil-Mabrouk/0-HITL-Template my-project
cd my-project
cp .env.example .env
# Éditer .env : SECRET_KEY, POSTGRES_*, SMTP_*, ADMIN_EMAIL, ADMIN_PASSWORD
```

### 2. Lancer en développement

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

- Frontend : http://localhost:5173
- Backend API : http://localhost:8000
- Docs API : http://localhost:8000/docs

### 3. Appliquer les migrations

```bash
docker-compose run --rm migrate alembic upgrade head
```

### 4. Déploiement production

```bash
cp .env.example .env.prod
# Éditer .env.prod avec toutes les variables de production
docker-compose -f docker-compose.prod.yml up -d
```

## Canaux d'Authentification

Activez les canaux souhaités dans `.env` :

```env
AUTH_CHANNEL_WAITLIST=true       # Liste d'attente avec invitations
AUTH_CHANNEL_DIRECT=false        # Inscription directe
AUTH_CHANNEL_ONBOARDING=false    # Inscription via questionnaire
```

## Monétisation

Deux modèles économiques, activables indépendamment via `.env` :

### Boutique de produits numériques (`MONETIZATION_SHOP=true`)

```env
MONETIZATION_SHOP=true
STRIPE_SECRET_KEY=sk_live_…
STRIPE_PUBLIC_KEY=pk_live_…
STRIPE_WEBHOOK_SECRET=whsec_…
DOWNLOAD_LINK_EXPIRE_HOURS=48
DOWNLOAD_MAX_ATTEMPTS=5
```

Flux : `POST /api/shop/checkout` → Stripe Checkout → webhook → email avec lien de téléchargement sécurisé.

### Abonnements premium (`MONETIZATION_SUBSCRIPTION=true`)

```env
MONETIZATION_SUBSCRIPTION=true
MONETIZATION_TRIAL_DAYS=14       # 0 = pas d'essai gratuit
STRIPE_SECRET_KEY=sk_live_…
STRIPE_WEBHOOK_SECRET=whsec_…
```

Flux : checkout → abonnement actif → rôle `premium` automatiquement accordé/retiré via webhooks Stripe.

**Configurer le webhook Stripe :**
```
https://api.votre-domaine.com/api/shop/webhook
Événements : checkout.session.completed, customer.subscription.*, invoice.payment_*
```

## Sécurité

Le `SecurityMiddleware` surveille en temps réel :
- Scans de chemins sensibles (`.git`, `.env`, `wp-*`, `.php`, etc.)
- User-agents de scanners connus (sqlmap, nikto, nmap, nuclei…)
- Tentatives d'injection (SQL, XSS, template, commande)

Tous les événements sont journalisés en base de données et consultables dans le Dashboard Admin → onglet **Sécurité**.

## Personnalisation du Template

```bash
# Remplacer les placeholders dans le projet
python scripts/replace_placeholders.py --root . --dry-run

# Placeholders disponibles :
# {{PROJECT_NAME}}, {{PROJECT_SLUG}}, {{PROJECT_DOMAIN}}
# {{PROJECT_DISPLAY_NAME}}, {{DEFAULT_EMAIL}}
```

## Variables d'Environnement Clés

| Variable | Description | Requis |
|---|---|---|
| `SECRET_KEY` | Clé JWT (openssl rand -hex 32) | Oui |
| `POSTGRES_USER/PASSWORD/DB` | Credentials PostgreSQL | Oui |
| `SMTP_HOST/USER/PASSWORD` | Serveur email | Oui (prod) |
| `ADMIN_EMAIL/PASSWORD` | Bootstrap admin | Recommandé |
| `AUTH_CHANNEL_*` | Canaux d'inscription actifs | Non |
| `MONETIZATION_SHOP` | Activer la boutique | Non |
| `MONETIZATION_SUBSCRIPTION` | Activer les abonnements | Non |
| `STRIPE_SECRET_KEY` | Clé secrète Stripe | Si monétisation |
| `STRIPE_WEBHOOK_SECRET` | Secret webhook Stripe | Si monétisation |

## Documentation

- [Architecture détaillée](docs/architecture.md)
- [Chapitre 01 — Infrastructure Docker](docs/chapters/chap_01.md)
- [Chapitre 03 — Modèles de données](docs/chapters/chap_03.md)
- [Chapitre 08 — Onboarding dynamique](docs/chapters/chap_08.md)
- [Chapitre 09 — Dashboard admin & analytics](docs/chapters/chap_09.md)
- [Chapitre 10 — SEO](docs/chapters/chap_10.md)
- [Chapitre 12 — Framework Agentic IA](docs/chapters/chap_12.md)
- [Chapitre 14 — Monétisation Stripe](docs/chapters/chap_14.md)

## Licence

MIT — Voir [LICENSE](LICENSE)

---

**Version** : 1.2.0 — **Dernière mise à jour** : 2026-03-26
