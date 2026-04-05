# 0-HITL — Agentic AI Platform Template

Template fullstack complet pour lancer une plateforme web avec gestion des utilisateurs, contenu, services d'IA agentique et monétisation intégrée.

**Stack** : FastAPI · PostgreSQL · React 19 · TypeScript · TailwindCSS · Docker · Traefik

---

## Fonctionnalités

| Domaine | Ce qui est inclus |
|---|---|
| **Auth** | JWT + refresh tokens, rôles hiérarchiques, vérification email, reset MDP |
| **Canaux d'inscription** | Waitlist avec invitations / Inscription directe / Onboarding questionnaire |
| **Contenu** | CMS Markdown, tutoriaux, leçons, accès premium |
| **Monétisation** | Boutique produits numériques + abonnements Stripe (feature flags) |
| **IA agentique** | Orchestrateur multi-agents, mémoire, garde-fous, dashboard |
| **Admin** | Utilisateurs, waitlist, analytics, sécurité, boutique |
| **SEO** | Sitemap dynamique, robots.txt, llms.txt, meta tags |
| **i18n** | Français / Anglais |
| **Infra** | Docker Compose (dev hot-reload + prod multi-stage), Traefik HTTPS auto |

---

## Démarrage rapide (Nouveau !)

Le template inclut désormais un CLI interactif pour configurer votre projet en moins de 2 minutes.

### Étape 1 — Cloner le projet

```bash
git clone https://github.com/your-org/0-hitl-template my-project
cd my-project
```

### Étape 2 — Initialisation interactive

Le CLI va vous poser quelques questions, générer vos clés secrètes, configurer votre `.env` et préparer votre dépôt Git.

```bash
# Installer les dépendances du CLI (si pas déjà fait)
pip install typer rich

# Lancer l'onboarding
python scripts/cli.py init
```

### Étape 3 — Lancer le développement

Une fois l'initialisation terminée, vous pouvez lancer l'environnement complet :

```bash
python scripts/cli.py dev
```

Cela démarre :
- **Frontend** → http://localhost:5173 (hot-reload Vite)
- **Backend**  → http://localhost:8000 (hot-reload Uvicorn)
- **Docs API** → http://localhost:8000/docs

---

## Commandes du CLI

Le script `scripts/cli.py` est votre centre de contrôle pour le développement quotidien :

| Commande | Description |
|---|---|
| `python scripts/cli.py init` | **Initialisation complète** (Placeholders, .env, Secrets, Git, Docker) |
| `python scripts/cli.py dev` | **Lancer** l'environnement Docker (Frontend + Backend + DB) |
| `python scripts/cli.py migrate` | **Appliquer les migrations** SQL (Alembic) |
| `python scripts/cli.py stop` | **Arrêter** tous les services Docker |

---

## Développement local (Manuel)

Si vous préférez ne pas utiliser le CLI, voici les commandes standards :

Cela démarre :
- **Frontend** → http://localhost:5173 (hot-reload Vite)
- **Backend**  → http://localhost:8000 (hot-reload Uvicorn)
- **Docs API** → http://localhost:8000/docs
- **PostgreSQL** → port 5433 (accès local)

### Appliquer les migrations (première fois ou après un `alembic revision`)

```bash
docker-compose -f docker-compose.dev.yml run --rm migrate
```

### Créer une nouvelle migration après modification des modèles

```bash
docker-compose -f docker-compose.dev.yml run --rm migrate alembic revision --autogenerate -m "description"
```

### Arrêter les services

```bash
docker-compose -f docker-compose.dev.yml down          # Arrêter
docker-compose -f docker-compose.dev.yml down -v       # Arrêter + supprimer les volumes
```

### Logs en temps réel

```bash
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f frontend
```

### Tests

```bash
# Backend (pytest, SQLite en mémoire — pas besoin de Docker)
cd backend
pip install -r requirements-test.txt
pytest                        # Tous les tests
pytest tests/unit/            # Tests unitaires uniquement
pytest tests/integration/     # Tests d'intégration uniquement
pytest --cov=app              # Avec couverture

# Frontend (Vitest + jsdom)
cd frontend
npm install
npm run test                  # One-shot
npm run test:watch            # Mode watch
npm run test:coverage         # Avec couverture
```

---

## Production

### Prérequis serveur

- VPS Ubuntu 22.04+ avec Docker et Docker Compose v2
- Domaine configuré avec deux entrées DNS :
  - `myapp.com` → IP du serveur
  - `api.myapp.com` → IP du serveur
- Ports 80 et 443 ouverts

### Étape 1 — Configurer Traefik (reverse proxy + HTTPS)

Traefik est géré en dehors de ce projet. Sur le serveur :

```bash
# Créer le réseau Docker partagé
docker network create proxy-net

# Lancer Traefik (une fois, globalement sur le serveur)
docker run -d \
  --name traefik \
  --network proxy-net \
  -p 80:80 -p 443:443 \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /etc/traefik:/etc/traefik \
  traefik:v3 \
  --api.insecure=false \
  --providers.docker=true \
  --providers.docker.exposedbydefault=false \
  --entrypoints.web.address=:80 \
  --entrypoints.websecure.address=:443 \
  --certificatesresolvers.letsencrypt.acme.email=contact@myapp.com \
  --certificatesresolvers.letsencrypt.acme.storage=/etc/traefik/acme.json \
  --certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web
```

### Étape 2 — Préparer le fichier de production

```bash
cp .env.example .env.prod
```

Remplir `.env.prod` avec les valeurs de production :

```env
ENVIRONMENT=production

# Base de données
POSTGRES_USER=myapp_prod
POSTGRES_PASSWORD=very_strong_random_password
POSTGRES_DB=myapp_prod

# JWT (OBLIGATOIRE : différent du dev !)
SECRET_KEY=generate_with_openssl_rand_hex_32

# Admin
ADMIN_EMAIL=admin@myapp.com
ADMIN_PASSWORD=AdminProdSecure@2026

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@myapp.com
SMTP_PASSWORD=gmail_app_password
EMAIL_FROM=noreply@myapp.com
EMAIL_FROM_NAME=My App

# Frontend URL (utilisé dans les emails)
FRONTEND_URL=https://myapp.com

# SEO
ROBOTS_ALLOW_INDEXING=true

# Monétisation (optionnel)
MONETIZATION_SHOP=false
MONETIZATION_SUBSCRIPTION=false
STRIPE_SECRET_KEY=sk_live_...
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Étape 3 — Déployer

```bash
# Construire et lancer en arrière-plan
docker-compose -f docker-compose.prod.yml up --build -d

# Appliquer les migrations
docker-compose -f docker-compose.prod.yml run --rm migrate

# Vérifier que les services tournent
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f backend
```

Le site est accessible sur `https://myapp.com` avec HTTPS automatique (Let's Encrypt).

### Mettre à jour en production

```bash
git pull origin main
docker-compose -f docker-compose.prod.yml up --build -d
docker-compose -f docker-compose.prod.yml run --rm migrate
```

### Sauvegarder la base de données

```bash
# Dump manuel
docker-compose -f docker-compose.prod.yml exec db \
  pg_dump -U myapp_prod myapp_prod > backup_$(date +%Y%m%d).sql

# Restaurer
cat backup_20260101.sql | docker-compose -f docker-compose.prod.yml exec -T db \
  psql -U myapp_prod myapp_prod
```

---

## Personnalisation

### Canaux d'authentification

Activez les canaux souhaités dans `.env` :

```env
AUTH_CHANNEL_WAITLIST=true       # Liste d'attente avec invitations admin
AUTH_CHANNEL_DIRECT=false        # Inscription directe sans invitation
AUTH_CHANNEL_ONBOARDING=false    # Inscription via questionnaire de profilage
```

### Style visuel (thème)

Le fichier `frontend/src/theme.config.ts` est le **point unique de contrôle** du style :

```typescript
const themeConfig = {
  preset:  'minimal',          // 'minimal' | 'vibrant' | 'glass' | 'brutal' | 'editorial'
  colors:  { primary, secondary, accent },
  fonts:   { heading, body, mono },
  geometry: 'rounded',         // 'sharp' | 'soft' | 'rounded' | 'pill'
  motion:   'smooth',          // 'none' | 'subtle' | 'smooth' | 'playful'
  effects:  { heroBackground, cardStyle, buttonStyle },
}
```

Pour un restyling assisté par IA, voir [`frontend_prompt.md`](frontend_prompt.md).

### Monétisation Stripe

```env
MONETIZATION_SHOP=true           # Boutique produits numériques
MONETIZATION_SUBSCRIPTION=true   # Abonnements (attribue le rôle `premium`)
MONETIZATION_TRIAL_DAYS=14       # Essai gratuit (0 = sans essai)
```

Configurer le webhook Stripe :
- URL : `https://api.myapp.com/api/shop/webhook`
- Événements : `checkout.session.completed`, `customer.subscription.*`, `invoice.payment_*`

---

## Structure du projet

```
.
├── project.json              ← Valeurs de personnalisation (à remplir en premier)
├── scripts/
│   └── setup_project.py      ← Script unique d'initialisation
├── backend/
│   ├── app/
│   │   ├── auth/             JWT, sécurité, dépendances
│   │   ├── routers/          Endpoints API (auth, users, admin, content, shop…)
│   │   ├── agents/           Framework IA (orchestrateur, mémoire, garde-fous)
│   │   ├── email/            Service SMTP + templates Jinja2
│   │   ├── middleware/        Sécurité, tracking
│   │   ├── models.py         Modèles SQLAlchemy
│   │   ├── config.py         Settings Pydantic (depuis .env)
│   │   └── main.py           App FastAPI
│   ├── alembic/              Migrations DB
│   ├── tests/                Tests pytest (unit + integration)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── theme.config.ts   ← Configuration visuelle centrale
│   │   ├── pages/            Toutes les pages React
│   │   ├── components/       Composants réutilisables
│   │   ├── context/          AuthContext
│   │   └── styles/presets/   Thèmes CSS (minimal, vibrant, glass…)
│   └── public/locales/       Traductions i18n (fr / en)
├── e2e/                      Tests Playwright
├── docker-compose.dev.yml    Développement (hot-reload)
├── docker-compose.prod.yml   Production (Traefik, HTTPS)
├── .env.example              Template des variables d'environnement
└── frontend_prompt.md        ← Prompt IA pour restyler le frontend
```

---

## Variables d'environnement clés

| Variable | Description | Requis |
|---|---|:---:|
| `SECRET_KEY` | Clé JWT — `openssl rand -hex 32` | ✅ |
| `POSTGRES_USER/PASSWORD/DB` | Credentials PostgreSQL | ✅ |
| `ADMIN_EMAIL/PASSWORD` | Compte admin initial | ✅ |
| `SMTP_HOST/PORT/USER/PASSWORD` | Serveur email sortant | ✅ prod |
| `FRONTEND_URL` | URL du frontend (pour les emails) | ✅ prod |
| `AUTH_CHANNEL_WAITLIST` | Activer la liste d'attente | ❌ |
| `AUTH_CHANNEL_DIRECT` | Activer l'inscription directe | ❌ |
| `MONETIZATION_SHOP` | Activer la boutique | ❌ |
| `MONETIZATION_SUBSCRIPTION` | Activer les abonnements | ❌ |
| `STRIPE_SECRET_KEY` | Clé secrète Stripe | Si monétisation |
| `STRIPE_WEBHOOK_SECRET` | Secret webhook Stripe | Si monétisation |
| `GEOIP_DB_PATH` | Chemin vers GeoLite2-City.mmdb | ❌ |

---

## Documentation technique

- [Architecture détaillée](docs/architecture.md)
- [Chapitre 01 — Infrastructure Docker](docs/chapters/chap_01.md)
- [Chapitre 03 — Modèles de données](docs/chapters/chap_03.md)
- [Chapitre 08 — Onboarding dynamique](docs/chapters/chap_08.md)
- [Chapitre 09 — Dashboard admin & analytics](docs/chapters/chap_09.md)
- [Chapitre 10 — SEO](docs/chapters/chap_10.md)
- [Chapitre 12 — Framework Agentic IA](docs/chapters/chap_12.md)
- [Chapitre 14 — Monétisation Stripe](docs/chapters/chap_14.md)
- [Chapitre 15 — Maintenance production](docs/chapters/chap_15.md)

---

## Licence

MIT — Voir [LICENSE](LICENSE)

**Version** : 1.3.0 · **Mise à jour** : 2026-03-28
