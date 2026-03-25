# 0-HITL — Zero-Human-In-The-Loop Agentic AI Platform Template

A production-ready, full-stack template for building web applications powered by autonomous AI agent services. Combines a **FastAPI** backend, **React/TypeScript** frontend, **PostgreSQL** database, and a modular **agentic AI framework** — all wired together and ready to ship.

---

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Feature Summary](#feature-summary)
4. [Project Structure](#project-structure)
5. [Quick Start](#quick-start)
6. [Environment Variables](#environment-variables)
7. [Development Commands](#development-commands)
8. [Authentication System](#authentication-system)
9. [API Reference](#api-reference)
10. [Database Models](#database-models)
11. [Agentic AI Framework](#agentic-ai-framework)
12. [Content Platform](#content-platform)
13. [Analytics & Tracking](#analytics--tracking)
14. [Adding a New Agent Service](#adding-a-new-agent-service)
15. [Frontend Pages](#frontend-pages)
16. [Docker & Deployment](#docker--deployment)
17. [Scripts](#scripts)
18. [License](#license)

---

## Overview

**0-HITL** is designed as a launchpad for AI-powered SaaS products. Rather than assembling boilerplate from scratch, you get a battle-tested stack with:

- A complete **user lifecycle** — waitlist, invitation, email verification, login, roles, profile, account deletion.
- A flexible **authentication channel** system — enable waitlist-only, direct signup, or a scored onboarding quiz, via environment variables.
- A **content management** system for publishing Markdown tutorials with role-gated access.
- A **pluggable agentic framework** with orchestrator, tool registry, memory, and guardrails.
- A fully wired **admin dashboard** — user management, analytics (world map, timeline, top countries), content editor, and database maintenance.
- Production Docker stack with **Traefik** reverse proxy and **Let's Encrypt** TLS — zero manual SSL configuration.

Customize placeholders with a single script and have a running SaaS scaffold in minutes.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend API | FastAPI 0.115+, Python 3.11+ |
| Database ORM | SQLAlchemy 2.x (sync), Alembic migrations |
| Database | PostgreSQL 16.3 |
| Auth | JWT (HS256), bcrypt (12 rounds), refresh tokens |
| Email | SMTP via Python `smtplib` (Gmail-compatible) |
| Rate Limiting | SlowAPI (Redis-free, in-process) |
| Geolocation | MaxMind GeoLite2 |
| Frontend | React 19, TypeScript 5.9, Vite 7.3 |
| UI / Styling | TailwindCSS 4.2, Radix UI, shadcn/ui |
| Charts | Recharts, react-simple-maps |
| i18n | i18next |
| Containerisation | Docker, Docker Compose |
| Reverse Proxy | Traefik v3 (production) |
| TLS | Let's Encrypt (ACME) |

---

## Feature Summary

### Backend

| Feature | Detail |
|---------|--------|
| JWT Authentication | Access token (15 min) + rotating refresh token (7 days), HttpOnly cookies |
| Role-Based Access Control | `anonymous → waitlist → user → premium → admin` hierarchy |
| Auth Channels | Switch between waitlist, direct, or onboarding registration via env vars |
| Email Service | Verification, password reset, invitation, welcome emails |
| Onboarding Engine | YAML-defined scored questionnaire → profile assignment + role upgrade |
| Content CMS | Tutorials + nested lessons, Markdown, role-gated access, SEO metadata |
| Admin Dashboard API | Stats, user management, activity audit log, content CRUD |
| Database Maintenance | Configurable retention policies, scheduled cleanup, VACUUM via admin API |
| Analytics | GeoIP-enriched page view tracking, country/timeline/city breakdowns |
| SEO | Dynamic `sitemap.xml` and `robots.txt` |
| Agentic Framework | Orchestrator, tool registry, guardrails, memory system |
| Rate Limiting | Per-route SlowAPI limits on all sensitive endpoints |
| Audit Logging | `ActivityLog` table for all significant user actions |
| GDPR | IP hashing, email anonymisation on account deletion, data retention controls |
| File Upload | Multi-type media upload (images, video, audio, PDF) up to 100 MB |

### Frontend

| Feature | Detail |
|---------|--------|
| Auth Flow | Login, register (waitlist/direct/onboarding), email verification, password reset |
| Route Guards | `PrivateRoute`, `GuestRoute`, `AdminRoute` wrappers |
| Learn Platform | Tutorial catalogue, lesson viewer with Markdown rendering |
| Admin Panel | Stats dashboard, user management table, content editor, waitlist manager |
| Agent Dashboard | Service card grid, execution launcher, history viewer |
| Internationalisation | i18next with JSON locale files (`en/common`, `en/auth`, `en/admin`) |
| Page Tracking | `usePageTracking` hook automatically fires on route changes |
| Responsive Design | TailwindCSS 4 + dark theme throughout |

---

## Project Structure

```
00-0-HITL-template/
│
├── backend/
│   ├── app/
│   │   ├── agents/                        # Agentic AI framework
│   │   │   ├── core/
│   │   │   │   ├── orchestrator.py        # Workflow execution engine
│   │   │   │   ├── tool_registry.py       # Tool discovery & execution
│   │   │   │   ├── guardrails.py          # Input/output safety checks
│   │   │   │   └── memory.py              # Short/long/contextual memory
│   │   │   ├── services/
│   │   │   │   └── template_service/      # Starter service skeleton
│   │   │   └── service_registry.py        # Loads agent_services.yaml
│   │   │
│   │   ├── auth/
│   │   │   ├── security.py                # bcrypt, JWT, email tokens
│   │   │   └── dependencies.py            # FastAPI dependency guards
│   │   │
│   │   ├── routers/
│   │   │   ├── auth.py                    # /api/auth/*
│   │   │   ├── users.py                   # /api/users/*
│   │   │   ├── admin.py                   # /api/admin/* (users, stats)
│   │   │   ├── admin_content.py           # /api/admin/tutorials|lessons|media
│   │   │   ├── admin_db.py                # /api/admin/db-settings|cleanup|vacuum
│   │   │   ├── agent_services.py          # /api/agent-services/*
│   │   │   ├── content.py                 # /api/content/* (public)
│   │   │   ├── waitlist.py                # /api/waitlist/*
│   │   │   ├── onboarding.py              # /api/onboarding/*
│   │   │   ├── tracking.py                # /api/track
│   │   │   ├── analytics.py               # /api/admin/analytics/*
│   │   │   ├── media.py                   # /api/admin/media/upload
│   │   │   └── seo.py                     # /sitemap.xml, /robots.txt
│   │   │
│   │   ├── schemas/                       # Pydantic request/response models
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── admin.py
│   │   │   ├── content.py                 # also contains make_slug()
│   │   │   ├── onboarding.py
│   │   │   └── waitlist.py
│   │   │
│   │   ├── services/
│   │   │   └── cleanup.py                 # Scheduled DB cleanup logic
│   │   │
│   │   ├── middleware/
│   │   │   └── tracking.py                # Injects IP/user into request.state
│   │   │
│   │   ├── email/
│   │   │   └── service.py                 # SMTP email sender
│   │   │
│   │   ├── geoip/
│   │   │   └── service.py                 # MaxMind GeoLite2 IP lookup
│   │   │
│   │   ├── onboarding/
│   │   │   ├── engine.py                  # Scores answers, assigns profiles
│   │   │   └── flows/
│   │   │       ├── 0hitl.json             # Default onboarding flow
│   │   │       └── politiqueia.json       # Example alternate flow
│   │   │
│   │   ├── config/
│   │   │   └── agent_services.yaml        # Agent service definitions
│   │   │
│   │   ├── models.py                      # All 14 SQLAlchemy models
│   │   ├── database.py                    # engine, SessionLocal, get_db
│   │   ├── config.py                      # Pydantic settings
│   │   ├── main.py                        # FastAPI app, CORS, routers, startup
│   │   ├── limiter.py                     # SlowAPI rate limiter instance
│   │   └── scheduler.py                   # APScheduler background tasks
│   │
│   ├── alembic/
│   │   └── versions/                      # Migration files
│   ├── Dockerfile                         # Production image
│   ├── Dockerfile.dev                     # Development image (hot reload)
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── agent-dashboard/
│   │   │   ├── DashboardLayout.tsx        # Agent services shell layout
│   │   │   └── ServiceCard.tsx            # Service tile component
│   │   ├── agent-services/                # Per-service UI components
│   │   ├── agent-commons/                 # Shared agent UI primitives
│   │   │
│   │   ├── pages/
│   │   │   ├── Landing.tsx                # Public home page
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx               # Invitation-based signup
│   │   │   ├── RegisterDirect.tsx         # Direct signup (channel-gated)
│   │   │   ├── ForgotPassword.tsx
│   │   │   ├── ResetPassword.tsx
│   │   │   ├── VerifyEmail.tsx
│   │   │   ├── Onboarding.tsx             # Scored onboarding quiz
│   │   │   ├── Profile.tsx                # Authenticated user profile
│   │   │   ├── Learn.tsx                  # Tutorial catalogue
│   │   │   ├── TutorialPage.tsx           # Tutorial detail + lesson list
│   │   │   ├── LessonPage.tsx             # Markdown lesson viewer
│   │   │   └── admin/
│   │   │       ├── Dashboard.tsx          # Admin overview
│   │   │       └── ContentEditor.tsx      # Tutorial/lesson CRUD
│   │   │
│   │   ├── auth/
│   │   │   └── AuthRouter.tsx             # Routes to correct signup channel
│   │   │
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   ├── WaitlistForm.tsx
│   │   │   ├── MarkdownRenderer.tsx       # ReactMarkdown wrapper
│   │   │   └── SEO.tsx                    # react-helmet head tags
│   │   │
│   │   ├── context/
│   │   │   └── AuthContext.tsx            # Global auth state & token management
│   │   │
│   │   ├── hooks/
│   │   │   └── usePageTracking.ts         # Auto-fires /api/track on navigation
│   │   │
│   │   ├── lib/
│   │   │   └── utils.ts
│   │   │
│   │   ├── App.tsx                        # React Router v7 route definitions
│   │   ├── main.tsx
│   │   └── i18n.ts                        # i18next initialisation
│   │
│   ├── public/
│   │   └── locales/en/
│   │       ├── common.json
│   │       ├── auth.json
│   │       └── admin.json
│   │
│   ├── Dockerfile                         # Production build (nginx)
│   ├── Dockerfile.dev                     # Dev server
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.ts
│
├── scripts/
│   ├── replace_placeholders.py            # Bulk-replace template placeholders
│   ├── rename_project.py                  # Rename project identifiers
│   └── backup-db.sh                       # PostgreSQL backup script
│
├── docs/
│   ├── architecture.md
│   └── chapters/                          # Extended documentation chapters
│
├── docker-compose.yml                     # Base service definitions
├── docker-compose.dev.yml                 # Development stack
├── docker-compose.prod.yml                # Production stack (Traefik + TLS)
├── .env.example                           # Environment variable template
└── CLAUDE.md                              # AI assistant instructions
```

---

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose 2.20+
- Node 20+ (for local frontend dev without Docker)
- Python 3.11+ (for local backend dev without Docker)

### 1 — Clone and configure

```bash
git clone https://github.com/Nabil-Mabrouk/0-HITL-Template.git my-project
cd my-project

# Copy and fill in your environment variables
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY, DATABASE_URL, SMTP_*, ADMIN_EMAIL, ADMIN_PASSWORD
```

Generate a secure `SECRET_KEY`:

```bash
openssl rand -hex 32
```

### 2 — (Optional) Customise placeholders

```bash
python scripts/replace_placeholders.py --root . --dry-run   # preview changes
python scripts/replace_placeholders.py --root .              # apply
```

Placeholders replaced:

| Placeholder | Default value | Replace with |
|-------------|---------------|--------------|
| `0-HITL` | Project name | Your project name |
| `0hitl` | Project slug | Your URL slug |
| `0-hitl.com` | Domain | Your domain |
| `ton@gmail.com` | Contact email | Your email |

### 3 — Start the development stack

```bash
docker-compose -f docker-compose.dev.yml up
```

| Service | URL |
|---------|-----|
| Frontend (Vite HMR) | http://localhost:5173 |
| Backend (auto-reload) | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |
| OpenAPI JSON | http://localhost:8000/openapi.json |
| PostgreSQL | localhost:5433 |

### 4 — Run database migrations

```bash
docker-compose -f docker-compose.dev.yml run --rm migrate alembic upgrade head
```

The admin account defined by `ADMIN_EMAIL` / `ADMIN_PASSWORD` is bootstrapped automatically on first startup.

---

## Environment Variables

Copy `.env.example` to `.env` and set each value. Variables marked **required** will prevent startup if missing.

### Application

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ | — | JWT signing key — minimum 32 bytes, generate with `openssl rand -hex 32` |
| `ENVIRONMENT` | | `development` | `development`, `staging`, or `production` |
| `PROJECT_NAME` | | `0hitl` | Internal project slug |
| `FRONTEND_URL` | | `http://localhost:5173` | Base URL used in email links |

### Database

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | ✅ | — | Full PostgreSQL DSN, e.g. `postgresql://user:pass@db:5432/0hitl` |
| `POSTGRES_USER` | | `postgres` | Used by the `db` Docker service |
| `POSTGRES_PASSWORD` | | — | PostgreSQL password |
| `POSTGRES_DB` | | `0hitl` | Database name |

### JWT Tokens

| Variable | Default | Description |
|----------|---------|-------------|
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |

### Admin Bootstrap

| Variable | Required | Description |
|----------|----------|-------------|
| `ADMIN_EMAIL` | ✅ | Email for the default admin account |
| `ADMIN_PASSWORD` | ✅ | Password for the default admin account |
| `ADMIN_FULL_NAME` | | Display name, defaults to `Admin` |

### SMTP (Email)

| Variable | Default | Description |
|----------|---------|-------------|
| `SMTP_HOST` | `smtp.gmail.com` | SMTP server host |
| `SMTP_PORT` | `587` | SMTP port (STARTTLS) |
| `SMTP_USER` | — | SMTP login (usually your email address) |
| `SMTP_PASSWORD` | — | App password (not your account password) |
| `EMAIL_FROM` | — | Sender address shown in emails |
| `EMAIL_FROM_NAME` | `0-HITL` | Sender display name |

### Authentication Channels

Three registration channels can be toggled independently:

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_CHANNEL_WAITLIST` | `true` | Enable waitlist-based invitations |
| `AUTH_CHANNEL_DIRECT` | `false` | Enable open direct signup |
| `AUTH_CHANNEL_ONBOARDING` | `false` | Enable scored onboarding quiz signup |

### Onboarding

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_ONBOARDING_FLOW` | `0hitl` | Flow filename in `app/onboarding/flows/` (without `.json`) |
| `AUTH_ONBOARDING_TARGET_ROLE` | `premium` | Role assigned after completing onboarding |

### GeoIP

| Variable | Default | Description |
|----------|---------|-------------|
| `GEOIP_DB_PATH` | `/app/geoip/GeoLite2-City.mmdb` | Path to MaxMind GeoLite2 database |

### SEO

| Variable | Default | Description |
|----------|---------|-------------|
| `ROBOTS_ALLOW_INDEXING` | `true` | Whether search engines can index the site |
| `ROBOTS_DISALLOW_PATHS` | `/admin,/profile,/api` | Comma-separated paths blocked from crawlers |

### Frontend (Vite)

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend base URL seen by the browser, e.g. `https://api.example.com` |

---

## Development Commands

### Backend

```bash
# Start dev server (hot reload via uvicorn --reload)
docker-compose -f docker-compose.dev.yml up backend

# Run all migrations
docker-compose -f docker-compose.dev.yml run --rm migrate alembic upgrade head

# Create a new migration after model changes
docker-compose -f docker-compose.dev.yml run --rm migrate \
  alembic revision --autogenerate -m "add column foo to users"

# Downgrade one migration
docker-compose -f docker-compose.dev.yml run --rm migrate alembic downgrade -1

# Open a Python shell inside the container
docker-compose -f docker-compose.dev.yml exec backend python

# Run tests
docker-compose -f docker-compose.dev.yml exec backend python -m pytest
```

### Frontend

```bash
# Dev server with HMR
cd frontend && npm run dev

# Type-check
cd frontend && npx tsc --noEmit

# Lint
cd frontend && npm run lint

# Production build
cd frontend && npm run build

# Preview production build locally
cd frontend && npm run preview
```

### Docker

```bash
# Start full dev stack
docker-compose -f docker-compose.dev.yml up

# Start in background
docker-compose -f docker-compose.dev.yml up -d

# Rebuild images after dependency changes
docker-compose -f docker-compose.dev.yml build

# Tail backend logs
docker-compose -f docker-compose.dev.yml logs -f backend

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Destroy volumes (wipes database)
docker-compose -f docker-compose.dev.yml down -v
```

---

## Authentication System

### Role Hierarchy

Roles are ordered hierarchically. A check for a lower role automatically passes for higher roles.

```
anonymous (0)  <  waitlist (1)  <  user (2)  <  premium (3)  <  admin (4)
```

Use `user.has_role(UserRole.premium)` to test whether a user meets or exceeds a role level.

### Token Flows

```
POST /api/auth/login
  → access_token  (JWT, 15 min, stored in localStorage)
  → refresh_token (opaque, 7 days, stored in DB + sent to browser)

POST /api/auth/refresh
  → new access_token
  → new refresh_token (old one is revoked — token rotation)

POST /api/auth/logout
  → refresh_token revoked in DB
```

### FastAPI Dependency Guards

Import these into any router to protect endpoints:

```python
from app.auth.dependencies import (
    get_current_user,     # Any active authenticated user
    get_verified_user,    # Authenticated + email verified
    get_optional_user,    # Returns None if not authenticated (for public + auth)
    require_admin,        # Admin role required
    require_premium,      # Premium or admin role required
    require_user,         # User, premium, or admin role required
)
```

Example:

```python
@router.get("/protected")
async def my_endpoint(current_user: User = Depends(get_verified_user)):
    return {"hello": current_user.full_name}
```

### Password Security

- bcrypt with 12 rounds
- Constant-time comparison (timing-attack resistant)
- Minimum 8 characters enforced at schema level
- Email tokens for verify/reset are single-use, expire in 24 hours

---

## API Reference

All endpoints are prefixed with `/api`. Interactive docs available at `/docs`.

### Auth — `/api/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | — | Register via waitlist invitation token |
| POST | `/auth/login` | — | Login, returns access + refresh tokens |
| POST | `/auth/refresh` | — | Rotate refresh token |
| POST | `/auth/verify-email` | — | Confirm email address |
| POST | `/auth/forgot-password` | — | Send password-reset email |
| POST | `/auth/reset-password` | — | Set new password with reset token |
| POST | `/auth/logout` | Bearer | Revoke refresh token |

Rate limit: 5 requests/minute on `/login` and `/register`.

### Users — `/api/users`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/users/me` | Bearer | Get own profile |
| PUT | `/users/me` | Bearer | Update `full_name` |
| PUT | `/users/me/password` | Bearer | Change password (revokes all sessions) |
| DELETE | `/users/me` | Bearer | Soft-delete account (anonymises email) |

### Waitlist — `/api/waitlist`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/waitlist` | — | Join waitlist (5/min, rejects disposable emails) |
| GET | `/waitlist/count` | — | Get total waitlist size |

### Onboarding — `/api/onboarding`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/onboarding/flow` | — | Get flow steps (scoring rules hidden) |
| POST | `/onboarding/evaluate` | — | Score answers, return profile + result |
| POST | `/onboarding/register` | — | Register with onboarding answers, assign role |

### Public Content — `/api/content`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/content/tutorials` | Optional | List published tutorials (filtered by role) |
| GET | `/content/tutorials/{slug}` | Optional | Tutorial detail with lesson list |
| GET | `/content/tutorials/{slug}/{lessonSlug}` | Optional | Lesson content (Markdown) |

> Access roles: tutorials can be set to `user`, `premium`, or `admin`. Anonymous visitors see only `user`-level content.

### Admin — Users & Stats — `/api/admin`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/admin/stats` | Admin | Platform statistics (users, waitlist counts) |
| GET | `/admin/users` | Admin | Paginated user list with search, role filter, show_deleted |
| PUT | `/admin/users/{id}/role` | Admin | Change user role |
| DELETE | `/admin/users/{id}` | Admin | Hard-delete user |
| GET | `/admin/waitlist` | Admin | Paginated waitlist entries |
| POST | `/admin/invite` | Admin | Send invitation email to a waitlist entry |
| POST | `/admin/reinvite/{id}` | Admin | Re-send invitation |
| GET | `/admin/activity-logs` | Admin | Paginated audit log |

### Admin — Content — `/api/admin`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/admin/tutorials` | Admin | List all tutorials (paginated) |
| POST | `/admin/tutorials` | Admin | Create tutorial |
| PUT | `/admin/tutorials/{id}` | Admin | Update tutorial |
| DELETE | `/admin/tutorials/{id}` | Admin | Delete tutorial + all lessons |
| GET | `/admin/tutorials/{id}/lessons` | Admin | List lessons for a tutorial |
| POST | `/admin/tutorials/{id}/lessons` | Admin | Create lesson |
| PUT | `/admin/lessons/{id}` | Admin | Update lesson content/order |
| DELETE | `/admin/lessons/{id}` | Admin | Delete lesson |
| POST | `/admin/media/upload` | Admin | Upload file (max 100 MB) |

### Admin — Database — `/api/admin`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/admin/db-settings` | Admin | Get retention policies |
| PUT | `/admin/db-settings` | Admin | Update retention settings |
| POST | `/admin/cleanup` | Admin | Trigger immediate cleanup |
| POST | `/admin/vacuum` | Admin | Run `VACUUM ANALYZE` (autocommit) |
| GET | `/admin/export/users` | Admin | Download users as ZIP (JSON + CSV) |

### Admin — Analytics — `/api/admin/analytics`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/admin/analytics/world` | Admin | All visits with country/city/coords |
| GET | `/admin/analytics/timeline` | Admin | Daily visit counts (configurable range) |
| GET | `/admin/analytics/top-countries` | Admin | Top 10 countries by visit count |

### Agent Services — `/api/agent-services`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/agent-services/services` | Bearer | List enabled services |
| GET | `/agent-services/services/{slug}` | Bearer | Service detail (agents, workflows, tools) |
| POST | `/agent-services/execute` | Bearer | Start a workflow execution |
| GET | `/agent-services/executions` | Bearer | Own execution history (paginated) |
| GET | `/agent-services/executions/{id}` | Bearer | Execution status + step details |
| POST | `/agent-services/executions/{id}/cancel` | Bearer | Cancel a running execution |
| GET | `/agent-services/tools` | Bearer | List registered tools |

### Tracking & SEO

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/track` | Optional | Record page view with GeoIP enrichment |
| GET | `/sitemap.xml` | — | Dynamic XML sitemap |
| GET | `/robots.txt` | — | Dynamic robots.txt |
| GET | `/health` | — | Health check (DB connectivity) |

---

## Database Models

The database has 14 tables, managed by Alembic migrations.

### Users & Auth

| Table | Key Columns | Notes |
|-------|-------------|-------|
| `users` | `id`, `email`, `hashed_password`, `full_name`, `role` (enum), `is_active`, `is_verified` | Soft delete anonymises email to `deleted_<uuid>@deleted.invalid` |
| `refresh_tokens` | `id`, `user_id`, `token` (hashed), `expires_at`, `revoked` | One row per active session |
| `activity_logs` | `id`, `user_id`, `action`, `ip_address`, `user_agent`, `details` | Audit trail |

### Waitlist & Onboarding

| Table | Key Columns | Notes |
|-------|-------------|-------|
| `waitlist_entries` | `id`, `email`, `created_at`, `invited_at`, `invitation_token` | |
| `user_profiles` | `id`, `user_id`, `flow_id`, `answers` (JSON), `profile`, `score` | Created during onboarding |

### Content

| Table | Key Columns | Notes |
|-------|-------------|-------|
| `tutorials` | `id`, `title`, `slug`, `description`, `cover_image`, `access_role`, `is_published`, `lang`, `tags` (JSON), `is_featured`, `views_count` | |
| `lessons` | `id`, `tutorial_id`, `title`, `slug`, `order`, `content` (Markdown), `duration_minutes`, `is_published` | |

### Analytics

| Table | Key Columns | Notes |
|-------|-------------|-------|
| `visits` | `id`, `ip_hash`, `country_code`, `country_name`, `region`, `city`, `latitude`, `longitude`, `path`, `user_id`, `user_role` | IP hashed for GDPR |
| `db_settings` | `id`, `tokens_retention_days`, `visits_retention_days`, `logs_retention_days`, `cleanup_frequency`, `last_cleanup_at` | Single-row settings |

### Agent Execution

| Table | Key Columns | Notes |
|-------|-------------|-------|
| `service_executions` | `id`, `user_id`, `service_slug`, `workflow_name`, `execution_id` (UUID), `input_params` (JSON), `status`, `result` (JSON), `execution_time_ms` | |
| `service_execution_steps` | `id`, `execution_id`, `step_id`, `agent_name`, `input_data`, `output_data`, `status`, `error_message`, `execution_time_ms` | One row per workflow step |
| `service_results` | `id`, `execution_id`, `result_type`, `content`, `file_path`, `file_url`, `file_size`, `mime_type`, `result_metadata` (JSON) | Structured output artefacts |
| `user_service_preferences` | `id`, `user_id`, `service_slug`, `preferences` (JSON), `is_favorite`, `last_used_at`, `usage_count` | Unique per user+service |

### Create a Migration

```bash
# After editing models.py
docker-compose -f docker-compose.dev.yml run --rm migrate \
  alembic revision --autogenerate -m "describe your change"

# Apply
docker-compose -f docker-compose.dev.yml run --rm migrate alembic upgrade head
```

---

## Agentic AI Framework

The framework lives in `backend/app/agents/` and is fully decoupled from the rest of the application.

### Service Registry

Services are declared in `backend/app/config/agent_services.yaml`:

```yaml
services:
  my_service:
    enabled: true
    name: "My Service"
    description: "What it does"
    agents:
      my_agent:
        name: "My Agent"
        model: "gpt-4"
        tools: ["web_search", "summarise"]
        system_prompt: "You are a helpful assistant..."
        temperature: 0.7
    workflows:
      main_workflow:
        steps:
          - name: "step_1"
            agent: "my_agent"
            description: "First step"
```

The `ServiceRegistry` singleton loads this file at startup.

### Orchestrator

`AgentOrchestrator` (`agents/core/orchestrator.py`) manages workflow execution:

- `execute_workflow(service_slug, workflow_name, params, user_id)` — starts execution asynchronously, returns an `execution_id`
- Steps run sequentially; each step's output is merged into a shared `context` dict
- `cancel_execution(execution_id)` — gracefully cancels a running workflow
- Status values: `pending → running → completed | failed | cancelled`

### Tool Registry

`ToolRegistry` (`agents/core/tool_registry.py`) is a central catalogue of callable functions:

```python
from app.agents.core.tool_registry import get_tool_registry

registry = get_tool_registry()

@registry.register(
    name="web_search",
    description="Search the web",
    category=ToolCategory.WEB,
    parameters=[ToolParameter("query", "string", "Search query", required=True)],
)
async def web_search(query: str) -> dict:
    ...
```

### Guardrails

`GuardrailSystem` (`agents/core/guardrails.py`) validates inputs and outputs at each step:

- **Prompt injection detection** — keyword and pattern matching
- **Toxic content filtering** — pattern-based hate speech / violence detection
- **Sensitive data detection** — PII patterns (email, credit card, SSN)
- **Rate limiting** — per-user, per-service request counting
- **Context length** — soft token estimation (4 chars ≈ 1 token)

### Memory System

`AgentMemory` (`agents/core/memory.py`) stores and retrieves keyed data:

| Memory Type | Default TTL | Use Case |
|-------------|-------------|----------|
| `SHORT_TERM` | 1 hour | Current session state |
| `LONG_TERM` | None (persistent) | User preferences, historical results |
| `CONTEXTUAL` | 30 minutes | Intermediate step outputs |

```python
memory = AgentMemory()
memory.store("user_goal", "Summarise arxiv papers", MemoryType.CONTEXTUAL, user_id=42)
entries = memory.retrieve(memory_type=MemoryType.CONTEXTUAL, user_id=42)
```

---

## Adding a New Agent Service

### 1 — Declare the service in YAML

```yaml
# backend/app/config/agent_services.yaml
services:
  email_writer:
    enabled: true
    name: "Email Writer"
    description: "Drafts professional emails"
    agents:
      drafter:
        model: "gpt-4"
        tools: ["tone_analyser"]
        system_prompt: "Draft a professional email based on the user's request."
        temperature: 0.5
    workflows:
      draft_email:
        steps:
          - name: "draft"
            agent: "drafter"
            description: "Create initial draft"
```

### 2 — Implement the agent logic

```python
# backend/app/agents/services/email_writer/agent.py
class EmailWriterAgent:
    async def run(self, input_data: dict, context: dict) -> dict:
        # Call your LLM here
        return {"draft": "Dear ...", "context_updates": {"draft_ready": True}}
```

### 3 — Register the agent with the orchestrator

Register your class in `backend/app/agents/services/__init__.py` or via the service registry hook.

### 4 — Add the frontend UI

```
frontend/src/agent-services/email_writer/
├── EmailWriterForm.tsx     # Input form
└── EmailWriterResult.tsx   # Output display
```

Add the service card to `agent-dashboard/DashboardLayout.tsx`.

### 5 — (Optional) Add custom tools

```python
@registry.register(name="tone_analyser", category=ToolCategory.ANALYSIS, ...)
async def tone_analyser(text: str) -> dict:
    ...
```

---

## Content Platform

Tutorials and lessons provide a role-gated knowledge base for your users.

### Access Roles

| `access_role` value | Who can read |
|---------------------|-------------|
| `user` | All logged-in users |
| `premium` | Premium and admin users |
| `admin` | Admin users only |

Anonymous visitors can see tutorial titles and descriptions but cannot access lesson content.

### Slug Generation

Slugs are auto-generated from titles using a diacritic-normalising function. The same algorithm is used in both the admin router and the content schemas to ensure consistency:

```
"Découvrir FastAPI" → "decouvrir-fastapi"
```

### Media Upload

Files uploaded via `POST /api/admin/media/upload` are stored in the `uploads/` directory (mounted as a Docker volume). Supported types: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.mp4`, `.webm`, `.mp3`, `.pdf`. Max size: 100 MB.

---

## Analytics & Tracking

### How It Works

1. The React `usePageTracking` hook fires `POST /api/track` on every route change.
2. The backend enriches the visit with GeoIP data (country, region, city, lat/lng) via MaxMind GeoLite2.
3. IP addresses are **hashed** (SHA-256) before storage for GDPR compliance.
4. Visits are cleaned up automatically based on `visits_retention_days` (configurable via admin UI).

### GeoIP Setup

Download the free GeoLite2-City database from [MaxMind](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data/) and set `GEOIP_DB_PATH` in your `.env`.

### Admin Analytics Endpoints

- **World map** — all visits with coordinates, suitable for react-simple-maps
- **Timeline** — daily visit count for the last N days (default 30)
- **Top countries** — top 10 countries by visit volume

---

## Docker & Deployment

### Development Stack (`docker-compose.dev.yml`)

| Service | Port | Description |
|---------|------|-------------|
| `frontend` | 5173 | Vite dev server with HMR |
| `backend` | 8000 | Uvicorn with `--reload` |
| `db` | 5433 | PostgreSQL 16.3 |
| `migrate` | — | Alembic one-shot migration runner |

### Production Stack (`docker-compose.prod.yml`)

Requires an external Traefik container on the `proxy-net` network.

| Service | Description |
|---------|-------------|
| `frontend` | Static React build, served via Traefik |
| `backend` | Gunicorn + Uvicorn workers, security-hardened (no new privileges, all capabilities dropped) |
| `db` | PostgreSQL 16.3-alpine, 512 MB memory limit |
| `migrate` | Runs `alembic upgrade head` at deploy time |

TLS certificates are obtained automatically via Let's Encrypt (`certresolver=letsencrypt`).

```bash
# Deploy to production
cp .env.example .env.prod   # fill in production values
docker-compose -f docker-compose.prod.yml up -d
```

### Scheduled Cleanup

The backend scheduler (`app/scheduler.py`) runs a cleanup job at a configurable interval:

- Expired refresh tokens
- Old page visits (based on `visits_retention_days`)
- Old activity logs (based on `logs_retention_days`)

Configure via `PUT /api/admin/db-settings`.

---

## Scripts

### `scripts/replace_placeholders.py`

Replaces template placeholders across all text files in the project. Safe: skips files >1 MB, binary files, `.git/`, and `node_modules/`.

```bash
# Preview what will change
python scripts/replace_placeholders.py --dry-run --root .

# Apply
python scripts/replace_placeholders.py --root .
```

Edit the `PLACEHOLDERS` dict in the script to map template values to your project values.

### `scripts/rename_project.py`

Batch-renames project identifiers. Useful for renaming the project slug across all files.

```bash
python scripts/rename_project.py "my_new_slug"
```

### `scripts/backup-db.sh`

Dumps the PostgreSQL database to a timestamped `.sql.gz` file.

```bash
bash scripts/backup-db.sh
# Output: backup_0hitl_20260325_143000.sql.gz
```

---

## License

MIT License — see [LICENSE](LICENSE).

---

**Version:** 1.1.0
**Last updated:** 2026-03-25
