# DecisionFlow AI

**Decision Operating System for Modern Organizations**

DecisionFlow AI transforms raw meeting transcripts into a fully structured execution layer — automatically extracting decisions, action items, risks, dependencies, and open questions using a 7-stage AI pipeline. Teams never lose track of what was decided, who owns what, and what is blocked.

---

## What It Does

| Problem | Solution |
|---|---|
| Decisions made in meetings never get executed | AI extracts every decision + assigns ownership automatically |
| Tasks fall through the cracks | 7-stage pipeline creates action items with owners and deadlines |
| No visibility into who is accountable | Reliability scores track execution rate per team member |
| Escalations happen too late | Automated 3-level escalation ladder with hourly Celery Beat scans |
| Can't find what was decided | Hybrid semantic + keyword search across all meeting memory |
| No insight into team performance | Real-time analytics dashboards for admins and workers |

---

## Tech Stack

| Layer | Technology |
|---|---|
| **API** | FastAPI (async) |
| **Database** | PostgreSQL + pgvector |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Migrations** | Alembic |
| **Task Queue** | Celery + Redis |
| **Event Bus** | Redis Streams |
| **AI Extraction** | Groq (Llama 3.1 70B) — free 14,400 req/day |
| **Embeddings** | Nomic Embed v1.5 — free 1M tokens/month |
| **File Storage** | Cloudflare R2 (S3-compatible, free 10GB) |
| **Email** | Resend.com (free 3,000 emails/month) |
| **Auth** | JWT + bcrypt + refresh token rotation |

---

## Architecture

```
DecisionFlow AI — Modular Monolith (DDD)
├── app/
│   ├── domains/
│   │   ├── identity/        # Auth, users, organizations, RBAC
│   │   ├── meetings/        # Upload, transcript storage, status FSM
│   │   ├── extraction/      # AI pipeline · decisions · tasks · risks
│   │   ├── graph/           # Task dependency DAG · Kahn cycle detection
│   │   ├── notifications/   # In-app · email · Slack · escalation ladder
│   │   ├── analytics/       # Reliability scores · dashboards · ROI
│   │   ├── search/          # Hybrid semantic + keyword search (RRF)
│   │   └── audit/           # Immutable append-only audit trail
│   └── shared/
│       ├── config.py        # Pydantic Settings
│       ├── database.py      # Async SQLAlchemy engine + RLS
│       ├── security.py      # JWT · bcrypt · token family rotation
│       ├── deps.py          # FastAPI dependencies · RBAC guards
│       ├── middleware.py    # CorrelationID · TenantContext · Logging
│       ├── events/          # Redis Streams producer + consumer
│       └── workers/         # Celery app + Beat tasks
├── migrations/              # Alembic versions
├── main.py                  # FastAPI composite root
├── pyproject.toml
├── alembic.ini
└── .env
```

Each domain follows a strict 4-layer structure:

```
domain/         → pure Python entities, value objects, abstract repos
application/    → use cases, commands, queries, services
infra/          → SQLAlchemy ORM, concrete repos, external adapters
api/            → FastAPI routes, Pydantic schemas, mappers
```

Dependency rule: `api → application → domain ← infra`

---

## AI Pipeline (7 Stages)

```
Raw Transcript
     │
     ▼
S1 Normalizer          → clean, detect speakers, chunk, hash
     │
     ▼
S2 Decision Extractor  → Groq/Llama → structured JSON decisions + confidence
     │
     ▼
S3 Action Extractor    → tasks, owner matching, deadline inference
     │
     ▼
S4 Dependency Detector → semantic dependencies → Kahn pre-validation (no cycles)
     │
     ▼
S5 Risk Analyzer       → ownership gaps, deadline conflicts, missing dependencies
     │
     ▼
S6 Embedder            → Nomic Embed → pgvector (768 dims) → memory chunks
     │
     ▼
S7 Question Extractor  → open questions flagged for follow-up
     │
     ▼
Persisted + Events Published + Analytics Computed
```

---

## AI Models (Free Tier)

| Task | Model | Provider | Free Limit |
|---|---|---|---|
| Extraction | Llama 3.1 70B | Groq | 14,400 req/day |
| Embeddings | nomic-embed-text-v1.5 | Nomic API | 1M tokens/month |

To get API keys:
- Groq: [console.groq.com](https://console.groq.com)
- Nomic: [atlas.nomic.ai](https://atlas.nomic.ai)

---

## Roles & Access

| Role | Access |
|---|---|
| `owner` | Full org access + billing |
| `admin` | All dashboards, all tasks, analytics, escalation management |
| `member` | Upload meetings, manage tasks, update decisions |
| `viewer` | Read-only access to meetings and decisions |

---

## Multi-Tenancy

- Every table has `org_id` column
- PostgreSQL Row Level Security (RLS) enforced at DB level
- `app.org_id` session variable set via middleware on every request
- pgvector queries **always pre-filter by org_id** — never post-filter

---

## Escalation Ladder

```
Task Overdue (Celery Beat — hourly)
     │
     ▼
Level 1 → Owner notified (in-app + email)
     │   (24h silence)
     ▼
Level 2 → Admins notified
     │   (24h more silence)
     ▼
Level 3 → Org owner notified
     │
     ▼
Admin resolves or dismisses via /escalations/{id}
```

---

## Reliability Score

```
reliability_score = (tasks_on_time / tasks_assigned) × 100

Refreshed hourly by Celery Beat
Cached on users.reliability_score for fast badge display
Score < 70  → At-risk user (flagged in admin dashboard)
Score ≥ 90  → Top performer
```

---

## Getting Started

### Prerequisites

```bash
Python 3.11+
PostgreSQL 15+ with pgvector extension
Redis 7+
```

### 1. Clone and install

```bash
git clone https://github.com/your-org/decisionflow-ai.git
cd decisionflow-ai
pip install -e ".[dev]"
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in the following in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/decisionflow
SYNC_DATABASE_URL=postgresql://user:pass@localhost:5432/decisionflow

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Auth
SECRET_KEY=your-secret-key-min-32-chars
REFRESH_SECRET_KEY=your-refresh-secret-key

# AI (free)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
NOMIC_API_KEY=nk-xxxxxxxxxxxxxxxxxxxx
AI_EXTRACTION_MODEL=llama-3.1-70b-versatile
AI_EMBEDDING_MODEL=nomic-embed-text-v1.5
AI_EMBEDDING_DIMS=768

# Storage (Cloudflare R2 — free 10GB)
S3_ENDPOINT_URL=https://<account_id>.r2.cloudflarestorage.com
S3_ACCESS_KEY_ID=your-r2-access-key
S3_SECRET_ACCESS_KEY=your-r2-secret-key
S3_BUCKET_NAME=decisionflow-transcripts

# Email (Resend.com — free 3000/month)
RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxx
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=DecisionFlow AI

# Slack (optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx/yyy/zzz

# App
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
```

### 3. Enable pgvector

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 4. Run migrations

```bash
alembic upgrade head
```

### 5. Start services

```bash
# API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Celery worker
celery -A app.shared.workers.celery_app worker --loglevel=info -Q pipeline,escalation,analytics,notifications

# Celery Beat (hourly scheduled tasks)
celery -A app.shared.workers.celery_app beat --loglevel=info
```

---

## API Overview

```
Auth
  POST /auth/register
  POST /auth/login
  POST /auth/refresh
  POST /auth/logout

Meetings
  POST /meetings                    → upload transcript
  GET  /meetings                    → list org meetings
  GET  /meetings/{id}
  DELETE /meetings/{id}

Extraction (after pipeline completes)
  GET  /meetings/{id}/extraction    → all entities for a meeting
  GET  /meetings/{id}/decisions
  GET  /meetings/{id}/tasks
  GET  /meetings/{id}/risks
  GET  /meetings/{id}/questions
  GET  /decisions                   → [admin] all org decisions
  GET  /tasks                       → [admin] all org tasks
  GET  /tasks/mine                  → [worker] my tasks
  PATCH /tasks/{id}/status
  PATCH /tasks/{id}/assign
  PATCH /decisions/{id}
  PATCH /risks/{id}/status
  PATCH /questions/{id}/answer

Graph
  GET  /meetings/{id}/graph         → dependency DAG
  GET  /tasks/{id}/dependencies
  POST /dependencies
  DELETE /dependencies/{id}

Search
  POST /search                      → hybrid semantic + keyword
  POST /search/suggest              → autocomplete

Notifications
  GET  /notifications               → my inbox
  GET  /notifications/unread        → unread count
  PATCH /notifications/{id}/read
  PATCH /notifications/read-all
  GET  /escalations                 → [admin]
  PATCH /escalations/{id}           → resolve/dismiss

Analytics
  GET  /analytics/dashboard         → [admin] org KPIs
  GET  /analytics/reliability       → [admin] all users
  GET  /analytics/reliability/{id}  → [admin] 30-day trend
  GET  /analytics/me                → [worker] my dashboard
  GET  /analytics/me/reliability    → my trend
  GET  /analytics/me/upcoming       → my upcoming deadlines

Audit
  GET  /audit-logs                  → [admin]
  GET  /audit-logs/{id}
```

---

## Project Status

| Module | Status |
|---|---|
| identity | ✅ Complete |
| meetings | ✅ Complete |
| extraction (pipeline) | ✅ Complete |
| graph | ✅ Complete |
| notifications | ✅ Complete |
| analytics | ✅ Complete |
| search | ✅ Complete |
| audit | ✅ Complete |
| shared (events, workers) | ✅ Complete |
| migrations | ✅ Complete |
| tests | ⏳ Pending |
| frontend | ⏳ Pending |

---

## License

MIT License — see `LICENSE` file.

---

Built with FastAPI · PostgreSQL · pgvector · Groq · Nomic Embed · Celery · Redis
