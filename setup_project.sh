#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " Inicializando Monorepo: Páramo Urbano (v2.0.0 Core)       "
echo "=========================================================="

# 1. Creación de directorios
mkdir -p docs/adr
mkdir -p data/seeds data/schemas data/fixtures
mkdir -p backend/src/core backend/src/domain/models backend/src/domain/physiological backend/src/domain/rules
mkdir -p backend/src/application/dtos backend/src/application/use_cases backend/src/application/interfaces
mkdir -p backend/src/infrastructure/database backend/src/infrastructure/parsers backend/src/infrastructure/queue backend/src/infrastructure/storage
mkdir -p backend/src/interfaces/api/v1 backend/src/interfaces/middlewares
mkdir -p backend/tests/unit backend/tests/integration backend/tests/e2e
mkdir -p frontend/src/api frontend/src/assets frontend/src/components/charts frontend/src/components/upload frontend/src/components/planner
mkdir -p frontend/src/views/onboarding frontend/src/views/diagnostics frontend/src/views/planner
mkdir -p frontend/src/store frontend/src/types frontend/tests
mkdir -p infra/docker/postgres infra/docker/nginx infra/scripts

# 2. Creación de .gitkeep en directorios clave
touch data/fixtures/.gitkeep
touch backend/tests/unit/.gitkeep
touch backend/tests/integration/.gitkeep
touch backend/tests/e2e/.gitkeep
touch frontend/tests/.gitkeep
touch infra/scripts/.gitkeep

# 3. Creación de .gitignore unificado
cat << 'EOF' > .gitignore
# Environment & Secrets
.env
.env.local
*.pem
*.key

# Dependencies
node_modules/
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
env/

# Build outputs
dist/
build/
*.egg-info/
.next/

# Telemetry raw uploads & Local Storage
uploads/
minio_data/
postgres_data/
redis_data/

# Logs & Diagnostics
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.coverage
htmlcov/
.pytest_cache/

# OS Specific
.DS_Store
Thumbs.db
.idea/
.vscode/
EOF

# 4. Placeholders de documentación para Agentes LLM
cat << 'EOF' > docs/PROJECT_OVERVIEW.md
# Páramo Urbano: Visión General del Proyecto

## Propósito
Plataforma SportTech de periodización determinista y telemetría para corredores de asfalto, trail runners y senderistas.

## Reglas Inmutables de Dominio
1. El cálculo de carga es estrictamente algorítmico y determinista (Banister EWMA: CTL ventana 42, ATL ventana 7, TSB = CTL - ATL).
2. Control lesivo: Sweet spot ACWR entre 0.8 y 1.3. Alarma y descanso obligatorio con ACWR > 1.5.
3. Sobrecarga progresiva: Los incrementos semanales de volumen no deben exceder el 10%.
4. Fecha objetivo (target_date): Bloqueo estricto de fechas menores a 14 días a futuro.
EOF

cat << 'EOF' > docs/DATA_SCHEMA.md
# Páramo Urbano: Especificación de Esquemas de Datos

## Rangos Fisiológicos Válidos
- Frecuencia Cardíaca: 30 a 240 bpm
- Altitud: -500 a 9.000 m
- Velocidad: 0 a 12.5 m/s

## Formatos Soportados
- FIT: SDK v21 binario (magic bytes: 0x2E 0x46 0x49 0x54).
- CSV: Compatible con exportaciones Strava, Garmin, Polar y estándar canónico.
- JSON: Esquema Canónico Kinkinpura/Páramo Urbano v1.
EOF

cat << 'EOF' > docs/ENGINEERING_GUIDELINES.md
# Guías de Ingeniería y Estándares de Código

- Arquitectura: Monolito modular con Clean Architecture / Hexagonal.
- Ingesta Asíncrona: Retorno HTTP 202 con job_id; worker independiente para procesamiento pesado.
- Cobertura de Tests: Unitarios en lógica matemática >= 90%.
- Git Commits: Conventional Commits (feat, fix, refactor, test, docs).
EOF

# 5. Placeholders de infraestructura
touch infra/docker/postgres/init.sql
touch README.md

echo "=========================================================="
echo " [OK] Estructura creada con éxito.                        "
echo " Siguientes pasos:                                        "
echo " 1. Copia las variables: cp .env.example .env             "
echo " 2. Inicia los servicios: docker compose up -d            "
echo "=========================================================="
