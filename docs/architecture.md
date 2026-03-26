# Architecture du Template Agentic AI — 0-HITL

## Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Frontend (React 19 / TS / Vite)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Landing  │ │ Learn /  │ │  Shop /  │ │ Premium  │ │  Admin   │  │
│  │          │ │ Lessons  │ │ Success  │ │          │ │Dashboard │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTPS (Traefik)
┌──────────────────────────────▼──────────────────────────────────────┐
│                     Backend (FastAPI)                                 │
│                                                                       │
│  Auth & Users │ Content CMS │ Shop & Sub │ Agentic IA │ Admin        │
│  ─────────────┼─────────────┼────────────┼────────────┼────────────  │
│  /api/auth    │ /api/content│ /api/shop  │ /api/svc   │ /api/admin   │
│  /api/users   │ /api/admin/ │ /api/sub   │ /api/agent │ /api/admin/  │
│               │  content    │ /api/shop/ │ _services  │  security    │
│               │             │  webhook   │            │ /api/admin/  │
│               │             │ /api/admin │            │  shop        │
│               │             │  /shop     │            │              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                     Infrastructure                                    │
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ PostgreSQL │  │  Stripe    │  │  SMTP Email │  │  GeoIP DB   │  │
│  │  Database  │  │  API       │  │  (Gmail…)   │  │  (MaxMind)  │  │
│  └────────────┘  └────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Composants Backend

### Routers API

| Fichier | Prefix | Rôle |
|---|---|---|
| `auth.py` | `/api/auth` | Login, register, refresh, verify, reset |
| `users.py` | `/api/users` | Profil utilisateur |
| `admin.py` | `/api/admin` | Gestion utilisateurs, waitlist |
| `waitlist.py` | `/api/waitlist` | Inscription liste d'attente |
| `onboarding.py` | `/api/onboarding` | Questionnaire + profilage |
| `content.py` | `/api/content` | Tutoriaux et leçons (lecture) |
| `admin_content.py` | `/api/admin/content` | CRUD contenu |
| `media.py` | `/api/media` | Upload/gestion fichiers |
| `shop.py` | `/api/shop` | Boutique : produits, checkout, téléchargement |
| `shop_webhook.py` | `/api/shop/webhook` | Webhook Stripe (signature HMAC vérifiée) |
| `subscription.py` | `/api/subscription` | Plans, checkout abonnement, portal, annulation |
| `admin_shop.py` | `/api/admin/shop` | CRUD produits, ventes, MRR, abonnements |
| `tracking.py` | `/api/track` | Collecte visites GeoIP |
| `analytics.py` | `/api/admin/analytics` | Stats visiteurs, world map |
| `security.py` | `/api/admin/security` | Événements d'intrusion |
| `admin_db.py` | `/api/admin/db` | Maintenance DB, VACUUM |
| `agent_services.py` | `/api/agent_services` | Exécution services IA |
| `seo.py` | `/sitemap.xml`, `/robots.txt` | SEO |

### Middleware

| Middleware | Rôle |
|---|---|
| `CORSMiddleware` | Gestion CORS (origines configurées) |
| `SecurityMiddleware` | Détection scanners, injections, chemins suspects |
| `SlowAPI` | Rate limiting par IP |

### Modèles de Données (SQLAlchemy)

```
users
 ├── refresh_tokens        (sessions JWT)
 ├── activity_logs         (audit)
 ├── user_profiles         (résultats onboarding)
 ├── purchases             (achats produits)
 ├── subscription          (abonnement Stripe, 1:1)
 └── security_events       (événements détectés)

products
 └── purchases

subscriptions → users

tutorials
 └── lessons

visits                      (tracking GeoIP anonymisé)
service_executions
 ├── service_execution_steps
 └── service_results
user_service_preferences
db_settings
security_events
```

## Système de Rôles

```
anonymous → waitlist → user → premium → admin
    0           1        2       3         4
```

- `premium` : accordé automatiquement à l'activation d'un abonnement Stripe ou manuellement par l'admin
- Les webhooks Stripe révoquent automatiquement `premium` en cas de non-paiement ou annulation

## Flux Monétisation

### Boutique (achat unique)
```
1. GET  /api/shop/products          → afficher le catalogue
2. POST /api/shop/checkout          → créer session Stripe Checkout
3.       [Stripe Hosted Page]       → paiement utilisateur
4. POST /api/shop/webhook           → checkout.session.completed
5.       _fulfill_shop_purchase()   → générer download_token, envoyer email
6. GET  /api/shop/download/{token}  → servir le fichier (vérifié + compté)
7. GET  /api/shop/purchases         → afficher dans le profil
```

### Abonnement (récurrent)
```
1. GET  /api/subscription/plans     → afficher les plans Stripe
2. POST /api/subscription/checkout  → créer session Stripe Checkout
3.       [Stripe Hosted Page]       → paiement utilisateur
4. POST /api/shop/webhook           → checkout.session.completed (mode=subscription)
5.       _fulfill_subscription()    → créer Subscription en DB, rôle → premium
6. POST /api/shop/webhook           → customer.subscription.updated/deleted
7.       _update/cancel_subscription() → sync statut, rôle → user si annulé
8. POST /api/subscription/portal    → Stripe Customer Portal (gérer, annuler)
```

## Système de Sécurité

```
Requête entrante
       ↓
SecurityMiddleware.dispatch()
       ├── chemin ignoré ? (/health, /api/track…) → pass
       ├── scanner UA ? (sqlmap, nikto…) → log SecurityEvent(scanner_detected, high)
       ├── chemin suspect ? (.git, .env, wp-*…)  → log SecurityEvent(path_scan, severity)
       └── injection dans URL/query ?             → log SecurityEvent(injection_attempt, critical)
       ↓
call_next(request)  ← jamais bloqué, monitoring uniquement

Admin Dashboard → /api/admin/security/events
               → /api/admin/security/summary (top IPs, by type/severity)
               → DELETE /api/admin/security/events/old (purge)
```

## Déploiement Docker

```
docker-compose.yml          ← squelette commun (réseaux, volumes, healthchecks)
docker-compose.dev.yml      ← hot-reload, ports exposés, volumes code
docker-compose.prod.yml     ← images optimisées, env_file, Traefik labels
```

Réseaux :
- `proxy-net` (externe, partagé avec Traefik) : frontend ↔ traefik, backend ↔ traefik
- `internal-net` (isolé) : backend ↔ db, migrate ↔ db

## Extensibilité

### Ajouter un service Agentic IA
1. `backend/config/agent_services.yaml` — définir le service et ses workflows
2. `backend/app/agents/services/<service>/` — implémenter les agents
3. `frontend/src/agent-services/<service>/` — ajouter l'UI
4. `backend/app/routers/agent_services.py` — enregistrer le router

### Ajouter un nouveau modèle
1. `backend/app/models.py` — créer la classe SQLAlchemy
2. `alembic revision --autogenerate -m "description"` — générer la migration
3. `alembic upgrade head` — appliquer

---

**Version** : 1.2.0 — **Dernière mise à jour** : 2026-03-26
