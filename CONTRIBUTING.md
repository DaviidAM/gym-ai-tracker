# Contributing to GymAI Tracker

Thank you for tu interés en contribuir a GymAI Tracker. Este documento te guía desde el primer paso hasta tu primer PR merged.

## Primeros pasos

### 1. Clonar el repositorio

```bash
git clone https://github.com/<tu-fork>/gymai-tracker.git
cd gymai-tracker
```

Si aún no tienes un fork, haz click en "Fork" en la página principal del repo.

### 2. Configurar el entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows
```

### 3. Instalar dependencias

```bash
pip install -e .
pip install pytest pytest-cov flake8
```

### 4. Verificar que todo funciona

```bash
pytest tests/ -v
flake8 src/
```

Si ambos comandos terminan sin errores, tu entorno está listo.

### 5. Crear una rama para tu cambio

```bash
git checkout -b feat/tu-nombre-de-feature
```

## Convenciones de código

### Python

- **Versión mínima:** Python 3.10
- **Linting:** `flake8` con configuración por defecto (max line length 79)
- **Type hints:** obligatorios en funciones públicas
- **Docstrings:** estilo Google para módulos y funciones públicas

```python
def calcular_rm(peso: float, repeticiones: int) -> float:
    """Calcula el Repetición Máxima estimada usando la fórmula de Brzycki.

    Args:
        peso: Peso levantado en kg.
        repeticiones: Número de repeticiones realizadas (1-12).

    Returns:
        Peso estimado para 1RM en kg.

    Raises:
        ValueError: si repeticiones está fuera del rango válido.
    """
    if not 1 <= repeticiones <= 12:
        raise ValueError("Repeticiones debe estar entre 1 y 12")
    return peso * (36 / (37 - repeticiones))
```

### Estructura de archivos

```
src/
    gymai_tracker/      # Paquete principal
        __init__.py
        tracking.py     # Lógica de tracking
        models.py       # Modelos de datos
        api.py          # Endpoints (si aplica)
tests/
    conftest.py         # Fixtures compartidos de pytest
    test_tracking.py
    test_models.py
docs/
    api.md              # Documentación de la API
```

### Nombres

| Elemento         | Convención          | Ejemplo                      |
|------------------|---------------------|------------------------------|
| Módulos          | `snake_case.py`     | `tracking_utils.py`          |
| Clases           | `CapWords`          | `TrainingSession`            |
| Funciones        | `snake_case`        | `calcular_rm`                |
| Constantes       | `UPPER_SNAKE_CASE`  | `MAX_REPETICIONES`           |
| Variables locales| `snake_case`        | `peso_maximo`                |

### Imports

Orden de secciones (cada una separada por una línea en blanco):
1. stdlib (`datetime`, `typing`, etc.)
2. terceros (`pytest`, `fastapi`, etc.)
3. locale (`gymai_tracker`)

```python
import datetime
from typing import Optional

import pytest
from fastapi import FastAPI

from gymai_tracker import models
```

## Flujo de trabajo con Git

### Ramas

```
main           <- código en producción
├── feat/      <- nuevas funcionalidades
├── fix/       <- correcciones
├── docs/      <- documentación
└── refactor/  <- refactors sin cambio de comportamiento
```

### Commits

Formato: `<tipo>(<alcance>): <descripción>`

Tipos: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

```bash
feat(tracking): añadir estimación de 1RM por fórmula de Brzycki
fix(models): corregir validación de peso negativo
docs(readme): actualizar tabla de características
```

### Pull Requests

1. **Abre un PR** contra `main` desde tu fork.
2. **Título:** describe el cambio en una línea (se usa como commit squash).
3. **Descripción del PR:** explica qué cambia y por qué.
4. **Checks:** los workflows de CI deben pasar (lint + tests).
5. **Reviews:** se requiere al menos 1 aprobación antes de merge.

#### Checklist antes de abrir PR

- [ ] `pytest tests/` pasa sin errores
- [ ] `flake8 src/` no reporta issues
- [ ] Los nuevos tests cubren el código nuevo
- [ ] La documentación está actualizada (si aplica)
- [ ] No hay secretos o credentials en el código

## Cómo correr los tests

```bash
# Todos los tests con coverage
pytest tests/ -v --cov=src --cov-report=term-missing

# Tests de un módulo específico
pytest tests/test_tracking.py -v

# Tests que contain una keyword
pytest -k "tracking" -v

# Modo watch (requiere pytest-watch)
ptw
```

## Documentación

- `docs/` contiene la documentación del proyecto.
- Actualiza los archivos relevantes si tu PR cambia comportamiento o APIs.
- No necesitas actualizar `docs/` para refactors puros o fixes que no cambien la API.

## Reportar issues

Si encuentras un bug o tienes una idea:

1. Busca en los issues existentes.
2. Si no existe, abre un nuevo issue con:
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Tu entorno (Python version, OS)

## Preguntas

Para preguntas generales usa la sección de Discussions del repo.
