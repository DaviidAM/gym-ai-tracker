# GymAI Tracker

Sistema de tracking de entrenamientos con inteligencia artificial para optimizar rutinas de gimnasio.

## Stack

- **Backend**: FastAPI + SQLite (aiosqlite) + SQLAlchemy 2.0 (async)
- **Frontend**: Astro + Tailwind CSS v4 + HTMX
- **DB Migrations**: Alembic

## Quick Start

### Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # dev server at http://localhost:4321
npm run build      # production build
```

### Seed Database

```bash
cd backend
python -m scripts.seed_db
```

## Arquitectura

```
gym-ai-tracker/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app entry
│   │   ├── config.py        # Settings (env vars)
│   │   ├── database.py      # AsyncEngine, session
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routers/         # API route modules
│   │   ├── schemas/         # Pydantic DTOs
│   │   └── services/        # Business logic
│   ├── alembic/             # DB migrations
│   ├── scripts/
│   │   └── seed_db.py       # Sample data seeder
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── layouts/         # Astro layouts
│   │   ├── pages/           # Route pages
│   │   └── styles/          # Global CSS
│   └── public/              # Static assets
└── scripts/                 # Root-level tooling
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/workouts/` | List workouts (JSON) |
| POST | `/workouts/` | Create workout (JSON) |
| GET | `/workouts/html/` | List workouts as HTML partial |
| GET | `/workouts/new` | New workout modal form (HTML) |
| GET | `/workouts/{id}` | Workout detail (JSON) |
| POST | `/workouts/{id}/sets` | Add set to workout (JSON) |
| GET | `/exercises/` | List exercises (JSON) |
| POST | `/exercises/` | Create exercise (JSON) |
| GET | `/exercises/html/` | List exercises as HTML partial |
| GET | `/exercises/new` | New exercise modal form (HTML) |
| GET | `/analytics/` | Analytics data (JSON) |

## Despliegue

### Railway

1. Crear proyecto en [Railway](https://railway.app)
2. Conectar repo de GitHub
3. Agregar variable de entorno: `DATABASE_URL=sqlite+aiosqlite:///./gymai.db`
4. Deploy automático en cada push a `main`

### Render

1. Crear Web Service en [Render](https://render.com)
2. pointing al directorio `backend`
3. Build command: `cd backend && pip install -e .`
4. Start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Fly.io

```bash
fly launch --image ghcr.io/<user>/gym-ai-tracker
fly secrets set DATABASE_URL="sqlite+aiosqlite:///./gymai.db"
fly deploy
```

## Configuración

Variables de entorno (backend/.env):

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./gymai.db` | Connection string |
| `SECRET_KEY` | `change-me-in-production` | JWT signing key |
| `OPENAI_API_KEY` | `""` | OpenAI API key (opcional) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT expiry |

## Características

- Tracking de entrenamientos con IA
- Normalización de nombres de ejercicios (sinónimos)
- Seguimiento de progreso con analytics
- Interfaz HTMX para actualizaciones parciales sin reload

## Licencia

Ver archivo LICENSE.
