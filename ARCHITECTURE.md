# GymAI Tracker — Arquitectura Tecnica

## Stack seleccionado

| Capa | Tecnologia | Justificacion |
|------|------------|---------------|
| Lenguaje | Python 3.11+ | Ecosistema maduro para ML/analytics, sintaxis legible |
| Backend | FastAPI | Validacion Pydantic nativa, async, autodoc Swagger/ReDoc |
| Base de datos | SQLite | Cero configuracion, portable, suficiente para MVP |
| ORM | SQLAlchemy 2.0 (async) | Estandar Python, tipado completo, soporte async |
| Schemas | Pydantic v2 | Validacion runtime con tipos Python nativos |
| Migrations | Alembic | Workflow versionado, integracion oficial SQLAlchemy |
| Auth | JWT + bcrypt | Sin estado, escalable horizontalmente |
| AI/Chat | LangChain + OpenAI | Abstraccion LLM, chain RAG sobre historial |
| Analytics | Pandas + Polars | Calculos de volumen/intensidad |
| Frontend | Astro + HTMX | SSG rapido, interactividad ligera sin JS pesado |
| Deploy backend | Railway / Render | Despliegue simple, PostgreSQL disponible |
| Deploy frontend | Netlify | CDN global, zero-config |


---

## Estructura de modulos (backend)

backend/
├── app/
│   ├── main.py              # FastAPI app, lifespan, CORS
│   ├── config.py            # Settings con Pydantic BaseSettings
│   ├── database.py          # SQLAlchemy async engine + session
│   ├── models/              # Modelos SQLAlchemy
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── workout.py
│   │   ├── exercise.py
│   │   └── progress.py
│   ├── schemas/             # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── workout.py
│   │   ├── exercise.py
│   │   └── progress.py
│   ├── routers/             # Endpoints por dominio
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── workouts.py
│   │   ├── exercises.py
│   │   └── analytics.py
│   ├── services/            # Logica de negocio
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── exercise_normalizer.py
│   │   ├── fitcron_scraper.py
│   │   └── chat.py
│   └── dependencies.py      # FastAPI dependencies (get_db, get_current_user)
├── alembic/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_workouts.py
│   └── test_exercises.py
└── pyproject.toml


### Dominios

| Modulo | Responsabilidad |
|--------|----------------|
| auth | Registro, login, verificacion JWT, refresh tokens |
| workouts | CRUD sesiones de entrenamiento, asociar ejercicios |
| exercises | Catalogo de ejercicios, normalizacion de nombres, sinonimos |
| progress | Registros de peso/volumen por ejercicio a lo largo del tiempo |


---

## Decisiones de diseno

### API first
Toda la logica expuesta via REST API. El frontend es un consumidor independiente.

### Async everywhere
FastAPI con SQLAlchemy async (aiosqlite). Sin endpoints bloqueantes.

### schemas models separation
- Pydantic schemas: validacion de entrada/salida de API
- SQLAlchemy models: representacion de datos persistidos
- Conversion explicita con .model_validate() y .model_dump()

### Auth con JWT stateless
Sin sesiones en servidor. El token JWT lleva user_id y exp. Refresh token rotates.

### Normalizacion de ejercicios
Tabla exercise_synonyms para resolver nombres libres a nombre canonico.

---

## Dependencias base (pyproject.toml)

toml
[project]
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
    "sqlalchemy[asyncio]>=2.0",
    "aiosqlite>=0.20",
    "alembic>=1.13",
    "pydantic>=2.9",
    "pydantic-settings>=2.6",
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
    "python-multipart>=0.0.20",
    "pandas>=2.2",
    "polars>=1.14",
    "httpx>=0.28",
    "langchain>=0.3",
    "langchain-openai>=0.2",
]


---

## Entorno local

```bash
cd backend
pip install -e .
uvicorn app.main:app --reload --port 8000
```

Swagger UI disponible en http://localhost:8000/docs.

---

*Ultima actualizacion: 2026-08-02*
