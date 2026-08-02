# GymAI Tracker — SPEC

## 1. Concept & Vision

**GymAI Tracker** es un asistente personal de gym que entiende lo que escribes, guarda tus entrenos, te muestra tu progreso con gráficos y te deja chatear con tu historial en lenguaje natural.

> Es como tener un entrenador personal que nunca olvida nada y te responde al instante.

## 2. Stack

| Layer | Technology |
|---|---|
| Frontend | Astro + HTMX (static-first, islands) |
| Backend | FastAPI (Python) |
| Database | SQLite |
| Analytics | Pandas / Polars |
| Chat / AI | LangChain + LLM |
| Media | Fitcron scraper (GIFs de ejercicios) |
| Deploy frontend | Netlify |
| Deploy backend | Railway / Render |

**No incluye PySpark** — queda para otro proyecto.

## 3. Data Model

```sql
-- Canonical exercise (e.g. "Bench Press")
exercises (id, name_canonical, muscle_group, gif_url, difficulty, equipment)

-- User's custom name for an exercise
exercise_synonyms (id, exercise_id, synonym)

-- A workout session
workouts (id, date, notes)

-- An exercise performed in a workout
workout_exercises (id, workout_id, exercise_id, sets, reps, weight_kg, rpe)
```

## 4. Features

### 4.1 Log Workout
Usuario escribe en texto libre:
```
"Hoy hice press de banca 5x5 a 80kg y fondos de triceps 4x12"
```
El sistema normaliza los nombres (synonyms), guarda en SQLite, y responde con un resumen.

### 4.2 Exercise Library
- Lista de ejercicios con GIF de Fitcron
- Crear ejercicio nuevo → búsqueda automática de GIF en Fitcron
- Fuzzy matching de nombres

### 4.3 Analytics Dashboard
- Volumen total por músculo (semana/mes)
- Progresión de peso en ejercicios clave
- Frecuencia de entrenos por semana
- Gráficos con Chart.js

### 4.4 AI Chat
Pregunta en lenguaje natural sobre tu historial:
```
"¿Cuánto he mejorado en press de banca este trimestre?"
```
LangChain recupera el contexto de SQLite y el LLM responde.

## 5. Pages

| Route | Description |
|---|---|
| `/` | Dashboard — último workout, stats rápidos |
| `/workouts` | Historial completo |
| `/workout/new` | Loguear nuevo entrenamiento |
| `/exercises` | Biblioteca de ejercicios |
| `/exercises/new` | Crear ejercicio + buscar GIF |
| `/analytics` | Gráficos de progreso |
| `/chat` | Chat con tu historial |

## 6. API Endpoints

```
POST /workouts              → crear workout
GET  /workouts              → listar workouts
GET  /workouts/{id}         → detalle workout

GET  /exercises             → listar ejercicios
POST /exercises             → crear ejercicio
GET  /exercises/search?q=   → fuzzy search

GET  /analytics/volume       → volumen por músculo
GET  /analytics/progression → progresión por ejercicio

POST /chat                  → LangChain chat
```

## 7. Fitcron Integration

Fitcron tiene 752 ejercicios con GIFs animados de alta calidad.

URL pattern:
```
https://fitcron.com/wp-content/uploads/{año}/{mes}/{id}-{nombre}_{musculo}_720.gif
```

Flujo:
1. Usuario crea ejercicio con nombre propio
2. Sistema busca en Fitcron por nombre
3. Muestra GIFs encontrados → usuario selecciona
4. GIF guardado en DB

## 8. Architecture

```
Browser
  ↓
Astro (Static + HTMX islands)
  ↓ HTTP → FastAPI
          ↓
    ┌─────┴──────┐
    ↓            ↓
 SQLite    Fitcron API
 (data)    (GIFs)
    ↓
 LangChain + LLM
```

## 9. Development Phases

### Phase 1 — Setup
- [ ] Repo + estructura de carpetas
- [ ] FastAPI + SQLite base
- [ ] Modelos SQLAlchemy
- [ ] SPEC.md completo

### Phase 2 — Core
- [ ] CRUD exercises
- [ ] CRUD workouts
- [ ] Normalización de nombres (synonyms)
- [ ] Fitcron scraper (buscar GIF)

### Phase 3 — Analytics
- [ ] Endpoints /analytics con Pandas
- [ ] Gráficos con Chart.js

### Phase 4 — Chat
- [ ] LangChain integration
- [ ] Endpoint /chat

### Phase 5 — Frontend
- [ ] Astro setup
- [ ] Todas las páginas

### Phase 6 — Deploy
- [ ] Backend en Railway/Render
- [ ] Frontend en Netlify
- [ ] Integración final
