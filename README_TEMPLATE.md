# {{PROJECT_DISPLAY_NAME}}

> **This is a project derived from the [0-HITL Agentic AI Platform Template](https://github.com/Nabil-Mabrouk/0-HITL-Template).**
> Replace this line with a one-sentence description of your project.

---

## Overview

*Describe your project here — what it does, who it is for, and what problem it solves.*

This application is built on the **0-HITL** template stack:

- **Backend** — FastAPI + SQLAlchemy + PostgreSQL + Alembic
- **Frontend** — React 19 + TypeScript + TailwindCSS + Vite
- **AI Services** — Modular agentic framework with orchestrator, tool registry, memory, and guardrails
- **Infrastructure** — Docker Compose (dev + prod), Traefik reverse proxy, Let's Encrypt TLS

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Environment Variables](#environment-variables)
3. [Development](#development)
4. [Project Structure](#project-structure)
5. [Authentication & Roles](#authentication--roles)
6. [Agent Services](#agent-services)
7. [Content Platform](#content-platform)
8. [Deployment](#deployment)
9. [License](#license)

---

## Getting Started

### Prerequisites

- Docker 24+ and Docker Compose 2.20+
- Node 20+ *(optional — for frontend dev without Docker)*
- Python 3.11+ *(optional — for backend dev without Docker)*

### 1 — Clone and configure

```bash
git clone <your-repo-url> {{PROJECT_SLUG}}
cd {{PROJECT_SLUG}}

cp .env.example .env
# Edit .env — see Environment Variables section below
```

Generate a secure `SECRET_KEY`:

```bash
openssl rand -hex 32
```

### 2 — Start the development stack

```bash
docker-compose -f docker-compose.dev.yml up
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5433 |

### 3 — Run database migrations

```bash
docker-compose -f docker-compose.dev.yml run --rm migrate alembic upgrade head
```

The admin account (`ADMIN_EMAIL` / `ADMIN_PASSWORD`) is created automatically on first startup.

---

## Environment Variables

Copy `.env.example` to `.env` and set these values before starting the app.

### Required

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | JWT signing secret — generate with `openssl rand -hex 32` |
| `DATABASE_URL` | PostgreSQL DSN, e.g. `postgresql://user:pass@db:5432/{{PROJECT_SLUG}}` |
| `ADMIN_EMAIL` | Default admin account email |
| `ADMIN_PASSWORD` | Default admin account password |

### SMTP (Email)

| Variable | Description |
|----------|-------------|
| `SMTP_HOST` | SMTP server (default: `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (default: `587`) |
| `SMTP_USER` | SMTP login |
| `SMTP_PASSWORD` | App password |
| `EMAIL_FROM` | Sender address |
| `EMAIL_FROM_NAME` | Sender display name |

### Authentication Channels

Enable the signup method that fits your product:

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_CHANNEL_WAITLIST` | `true` | Invitation-based signup |
| `AUTH_CHANNEL_DIRECT` | `false` | Open signup |
| `AUTH_CHANNEL_ONBOARDING` | `false` | Scored questionnaire signup |

### Application

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | `development`, `staging`, or `production` |
| `FRONTEND_URL` | `http://localhost:5173` | Base URL used in email links |
| `VITE_API_URL` | `http://localhost:8000` | Backend URL seen by the browser |
| `GEOIP_DB_PATH` | `/app/geoip/GeoLite2-City.mmdb` | Path to MaxMind GeoLite2 database |
| `ROBOTS_ALLOW_INDEXING` | `true` | Allow search engine crawling |

---

## Development

### Backend

```bash
# Start backend only
docker-compose -f docker-compose.dev.yml up backend

# Create a migration after editing models.py
docker-compose -f docker-compose.dev.yml run --rm migrate \
  alembic revision --autogenerate -m "describe your change"

# Apply migrations
docker-compose -f docker-compose.dev.yml run --rm migrate alembic upgrade head

# Run tests
docker-compose -f docker-compose.dev.yml exec backend python -m pytest
```

### Frontend

```bash
cd frontend

npm run dev        # Dev server with hot module replacement
npm run build      # Production build
npm run lint       # ESLint
npx tsc --noEmit   # Type-check without building
```

### Useful Docker commands

```bash
# Rebuild after dependency changes
docker-compose -f docker-compose.dev.yml build

# View backend logs
docker-compose -f docker-compose.dev.yml logs -f backend

# Destroy everything (including database volume)
docker-compose -f docker-compose.dev.yml down -v
```

---

## Project Structure

```
{{PROJECT_SLUG}}/
│
├── backend/
│   ├── app/
│   │   ├── agents/                  # Agentic AI framework
│   │   │   ├── core/
│   │   │   │   ├── orchestrator.py  # Workflow execution engine
│   │   │   │   ├── tool_registry.py # Tool discovery & execution
│   │   │   │   ├── guardrails.py    # Safety & validation
│   │   │   │   └── memory.py        # Agent memory (short/long/contextual)
│   │   │   ├── services/            # Your agent service implementations
│   │   │   └── service_registry.py  # Loads agent_services.yaml
│   │   │
│   │   ├── auth/                    # JWT, bcrypt, dependency guards
│   │   ├── routers/                 # All API endpoints
│   │   ├── schemas/                 # Pydantic request/response models
│   │   ├── email/                   # SMTP email service
│   │   ├── geoip/                   # MaxMind GeoIP lookup
│   │   ├── onboarding/              # Onboarding engine + flow configs
│   │   ├── middleware/              # Request tracking middleware
│   │   ├── services/                # Background cleanup service
│   │   ├── config/
│   │   │   └── agent_services.yaml  # Agent service definitions
│   │   ├── models.py                # SQLAlchemy database models
│   │   ├── database.py              # DB connection + session factory
│   │   ├── config.py                # Pydantic settings
│   │   └── main.py                  # FastAPI app entry point
│   │
│   ├── alembic/versions/            # Database migration files
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── agent-dashboard/         # Agent service shell UI
│   │   ├── agent-services/          # Per-service UI components
│   │   ├── agent-commons/           # Shared agent UI primitives
│   │   ├── pages/                   # React pages
│   │   ├── components/              # Reusable UI components
│   │   ├── context/AuthContext.tsx  # Global auth state
│   │   ├── hooks/                   # Custom React hooks
│   │   └── App.tsx                  # Route definitions
│   │
│   ├── public/locales/              # i18n translation files
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   └── package.json
│
├── scripts/
│   ├── replace_placeholders.py      # Bulk replace template placeholders
│   ├── rename_project.py            # Rename project identifiers
│   └── backup-db.sh                 # PostgreSQL backup
│
├── docker-compose.dev.yml           # Development stack
├── docker-compose.prod.yml          # Production stack (Traefik + TLS)
└── .env.example                     # Environment variable template
```

---

## Authentication & Roles

### Role Hierarchy

```
anonymous  <  waitlist  <  user  <  premium  <  admin
```

Roles are hierarchical — a check for `user` passes for `premium` and `admin` as well.

### Registration Channels

| Channel | Env flag | Flow |
|---------|----------|------|
| Waitlist | `AUTH_CHANNEL_WAITLIST=true` | Admin invites users from the waitlist |
| Direct | `AUTH_CHANNEL_DIRECT=true` | Open signup, assigns `user` role |
| Onboarding | `AUTH_CHANNEL_ONBOARDING=true` | Scored quiz, assigns role based on result |

### Protecting Endpoints

```python
from app.auth.dependencies import require_admin, require_premium, get_verified_user

@router.get("/my-endpoint")
async def protected(current_user: User = Depends(require_premium)):
    ...
```

---

## Agent Services

### Defining a Service

Edit `backend/app/config/agent_services.yaml`:

```yaml
services:
  my_service:
    enabled: true
    name: "My Service"
    description: "What it does"
    agents:
      my_agent:
        model: "gpt-4"
        tools: ["web_search"]
        system_prompt: "You are a helpful assistant."
        temperature: 0.7
    workflows:
      main_workflow:
        steps:
          - name: "step_1"
            agent: "my_agent"
            description: "Execute the main task"
```

### Workflow Execution

```
POST /api/agent-services/execute
{
  "service_slug": "my_service",
  "workflow_name": "main_workflow",
  "params": { "user_input": "..." }
}

→ { "execution_id": "uuid-..." }

GET /api/agent-services/executions/{execution_id}
→ { "status": "completed", "steps": [...], "result": {...} }
```

### Available Framework Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `AgentOrchestrator` | `agents/core/orchestrator.py` | Run multi-step workflows |
| `ToolRegistry` | `agents/core/tool_registry.py` | Register and execute tools |
| `GuardrailSystem` | `agents/core/guardrails.py` | Validate inputs/outputs |
| `AgentMemory` | `agents/core/memory.py` | Short/long/contextual memory |

---

## Content Platform

Publish tutorials with nested Markdown lessons and role-gated access.

### Access Roles

| `access_role` | Visible to |
|---------------|-----------|
| `user` | All logged-in users |
| `premium` | Premium + admin only |
| `admin` | Admin only |

### API

```
GET  /api/content/tutorials                 List published tutorials
GET  /api/content/tutorials/{slug}          Tutorial + lesson list
GET  /api/content/tutorials/{slug}/{lesson} Lesson content (Markdown)

# Admin CRUD
POST /api/admin/tutorials
PUT  /api/admin/tutorials/{id}
POST /api/admin/tutorials/{id}/lessons
PUT  /api/admin/lessons/{id}
POST /api/admin/media/upload               Upload media files (max 100 MB)
```

---

## Deployment

### Production

```bash
cp .env.example .env.prod
# Fill in production values

docker-compose -f docker-compose.prod.yml up -d
```

Requires an external **Traefik** container on a shared `proxy-net` Docker network. TLS certificates are obtained automatically from Let's Encrypt.

### Migrations at Deploy Time

The `migrate` service in `docker-compose.prod.yml` runs `alembic upgrade head` automatically on every deployment before the backend starts.

### Database Backup

```bash
bash scripts/backup-db.sh
# Creates: backup_{{PROJECT_SLUG}}_YYYYMMDD_HHMMSS.sql.gz
```

---

## API Quick Reference

| Area | Base Path |
|------|-----------|
| Authentication | `POST /api/auth/{login,register,refresh,logout,...}` |
| User profile | `GET/PUT/DELETE /api/users/me` |
| Admin — users | `GET/PUT/DELETE /api/admin/users` |
| Admin — content | `GET/POST/PUT/DELETE /api/admin/tutorials` |
| Admin — analytics | `GET /api/admin/analytics/{world,timeline,top-countries}` |
| Agent services | `GET/POST /api/agent-services/{services,execute,executions}` |
| Public content | `GET /api/content/tutorials` |
| Waitlist | `POST /api/waitlist` |
| SEO | `GET /sitemap.xml`, `GET /robots.txt` |
| Health | `GET /health` |

Full interactive docs: **http://localhost:8000/docs**

---

## License

MIT License — see [LICENSE](LICENSE).

---

*Scaffolded from [0-HITL Template](https://github.com/Nabil-Mabrouk/0-HITL-Template) — version 1.1.0*
