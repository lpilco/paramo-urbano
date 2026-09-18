# Páramo Urbano (v2.0.0 Core)

> **«Donde el asfalto toca la cumbre»**  
> *Telemetría determinista y periodización adaptativa para atletas de asfalto, trail running y montañismo andino.*

---

[![MVP Status](https://img.shields.io/badge/MVP_Release-v2.0.0--core-emerald?style=for-the-badge&logo=git)](https://github.com/lpilco/paramo-urbano)
[![Quality Gate](https://img.shields.io/badge/Quality_Gate-Passing_100%25-brightgreen?style=for-the-badge&logo=checkmarx)](https://github.com/lpilco/paramo-urbano)
[![Tests Passing](https://img.shields.io/badge/Tests-308_Passed-success?style=for-the-badge&logo=pytest)](https://github.com/lpilco/paramo-urbano)
[![Architecture](https://img.shields.io/badge/Architecture-Clean_Arch_%26_DDD-blue?style=for-the-badge)](https://github.com/lpilco/paramo-urbano)
[![Python](https://img.shields.io/badge/Backend-Python_3.11+_|_FastAPI-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/Frontend-React_18_|_TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://react.dev)
[![Docker](https://img.shields.io/badge/Infrastructure-PostgreSQL_|_Redis_|_MinIO-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![Proprietary](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)](https://github.com/lpilco/paramo-urbano)

---

## 🏔️ 1. Visión y Propósito

El atleta andino contemporáneo habita una dualidad biológica única: entrena en el rigor plano y de alta cadencia del pavimento urbano, pero compite o busca superarse en senderos agrestes, pasos de alta montaña y cumbres que superan los 4.000 msnm.

Las plataformas analíticas tradicionales (Strava, TrainingPeaks, V.O2) ignoran sistemáticamente el impacto excéntrico del desnivel acumulado (+D), la respuesta hipóxica por altitud barométrica o imponen barreras económicas y metodológicas.

**Páramo Urbano** resuelve esta brecha combinando ingeniería de datos de alta precisión con fisiología deportiva estricta:

* **Dualidad Biológica Andina:** Pondera la equivalencia articular entre la monotonía de asfalto y el desgaste neuromuscular de descensos técnicos en montaña.
* **Rigor Determinista Absoluto (Cero Conjeturas):** Queda estrictamente prohibido delegar el cálculo de carga, fatiga o prescripción a modelos estocásticos (LLMs). Todo cómputo se rige por formulaciones matemáticas auditables y reproducibles:
  * **Banister EWMA:** Carga Crónica de Entrenamiento / Fitness ($CTL$, $\tau_1 = 42\text{ días}$), Carga Aguda de Entrenamiento / Fatiga ($ATL$, $\tau_2 = 7\text{ días}$) y Balance de Estrés / Rendimiento ($TSB = CTL - ATL$).
  * **Gabbett ACWR (Acute:Chronic Workload Ratio):** Detección temprana del riesgo de sobreentrenamiento con *sweet spot* entre $0.8$ y $1.3$, y activación obligatoria de alerta y descanso forzoso cuando $ACWR > 1.5$.
  * **Foster sRPE:** Cuantificación estandarizada para atletas debutantes mediante la escala Session-RPE ($Carga = \text{Duración [min]} \times \text{RPE [1-10]}$).
  * **Jack Daniels VDOT & Corrección Altitudinal:** Estimación fisiológica de ritmos de entrenamiento adaptados al perfil hipóxico del corredor.
* **Privacidad y Soberanía de Datos:** Protección integral mediante ofuscación de coordenadas sensibles de origen y destino (*Privacy Geofencing*) en toda telemetría procesada.

---

## 📐 2. Arquitectura del Monorepo

El proyecto está diseñado bajo los principios de **Clean Architecture**, **Domain-Driven Design (DDD)** y desacoplamiento modular estricto:

```text
paramo-urbano/
├── docs/                        # PRD v2.0.0, Decisiones de Arquitectura (ADR) y directrices
│   ├── adr/                     # Architectural Decision Records formales
│   ├── PRD.md                   # Documento de Requerimientos de Producto y Especificaciones
│   └── PROJECT_OVERVIEW.md      # Reglas inmutables de dominio fisiológico
├── data/                        # Fixtures de telemetría y scripts de sembrado
│   ├── fixtures/                # Muestras reales de telemetría (.FIT, .GPX, .CSV)
│   └── seeds/                   # Perfiles andinos y planes de entrenamiento semilla
├── backend/                     # Clean Architecture en 4 capas estrictas (Python 3.11+)
│   ├── src/
│   │   ├── domain/              # Dominio puro sin dependencias (Entidades, VOs, Banister, ACWR)
│   │   ├── application/         # Casos de uso (ParseActivity, CalculateLoad, IngestionWorker)
│   │   ├── infrastructure/      # Adaptadores I/O (SQLAlchemy, Redis, MinIO S3, FIT SDK)
│   │   └── interfaces/          # REST API con FastAPI v1, routers, middlewares y schemas
│   └── tests/                   # Suite de pruebas automatizadas (Unitarias, Integración, E2E)
│       ├── unit/                # 100% pure domain & math tests
│       ├── integration/         # DB, Redis Queue y Object Storage
│       └── e2e/                 # Flujos de API y criterios de aceptación del PRD
├── frontend/                    # SPA responsiva moderna (React 18 + TypeScript + Vite)
│   ├── src/
│   │   ├── components/          # Componentes modulares accesibles (WCAG 2.1 AA)
│   │   ├── views/               # Onboarding bifurcado, Dashboard Telemetría, Periodización
│   │   ├── services/            # Clientes HTTP API y persistencia de sesión
│   │   └── styles/              # Tokens de diseño y CSS modular responsivo
│   └── tests/                   # Pruebas de integración de interfaz
├── infra/                       # Infraestructura como código y orquestación local
│   ├── docker/
│   │   ├── docker-compose.yml   # PostgreSQL 16, Redis 7 y MinIO S3
│   │   ├── nginx/               # Reverse proxy y balanceador
│   │   └── postgres/            # Scripts de inicialización DDL y extensiones
│   └── scripts/                 # Utilidades de mantenimiento y despliegue
├── .agents/                     # Directrices de ingeniería para agentes de IA (Clean Code & DDD)
├── .env.example                 # Plantilla de variables de entorno del sistema
└── README.md                    # Manifiesto y documentación técnica raíz
```

---

## ⚙️ 3. Requisitos Previos y Variables de Entorno

### Requisitos del Sistema
* **Docker & Docker Compose** (Docker 24.0+, Compose v2.20+)
* **Python 3.11+** (con gestor de paquetes `pip` y `venv`)
* **Node.js 20+** & **npm 10+**
* **Git 2.40+**

### Configuración de Variables de Entorno

Clona la plantilla base a tu archivo local `.env`:

```bash
cp .env.example .env
```

| Variable | Propósito | Valor por Defecto Local |
| :--- | :--- | :--- |
| `NODE_ENV` | Entorno de ejecución | `development` |
| `APP_PORT` | Puerto de escucha Backend API | `4000` |
| `FRONTEND_PORT`| Puerto local del servidor Vite | `3000` |
| `DB_HOST` / `DB_PORT` | Conexión a PostgreSQL | `localhost` / `5432` |
| `DB_NAME` / `DB_USER` | Nombre y usuario de base de datos | `paramo_db` / `paramo_admin` |
| `DB_PASSWORD` | Contraseña transaccional | `paramo_secure_pass` |
| `REDIS_HOST` / `REDIS_PORT`| Host y puerto del broker Redis | `localhost` / `6379` |
| `MINIO_PORT` / `MINIO_CONSOLE_PORT` | Puertos S3 API y consola web MinIO | `9000` / `9001` |
| `JWT_SECRET` | Llave simétrica de firma de tokens JWT | *(Definida en .env)* |
| `MAX_UPLOAD_FILE_SIZE_BYTES` | Límite máximo de carga por archivo (.FIT/.GPX) | `26214400` (25 MB) |

---

## 🚀 4. Guía de Despliegue Local Rápido

Sigue estos 4 pasos para poner en marcha el stack completo en tu estación de trabajo:

### Paso 1: Levantar Servicios de Persistencia y Colas
Despliega los contenedores de PostgreSQL 16, Redis 7 y MinIO S3:

```bash
docker compose -f infra/docker/docker-compose.yml up -d
```

Verifica la salud de los servicios:
```bash
docker compose -f infra/docker/docker-compose.yml ps
```

### Paso 2: Configurar y Sembrar el Backend

Crea el entorno virtual e instala las dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e backend/
```

Ejecuta el sembrado determinista de perfiles andinos, actividades históricas y metas de entrenamiento:

```bash
python -m backend.src.infrastructure.database.seeds
```

Inicia la API REST de FastAPI en modo recarga rápida:

```bash
uvicorn backend.src.interfaces.api.main:app --host 0.0.0.0 --port 4000 --reload
```
*Documentación interactiva disponible en: `http://localhost:4000/docs`*

### Paso 3: Iniciar el Worker de Telemetría en Segundo Plano (Opcional para procesamiento masivo)

En una terminal secundaria activa:

```bash
source .venv/bin/activate
python -m backend.src.infrastructure.queue.worker
```

### Paso 4: Levantar el Frontend SPA

En una tercera terminal:

```bash
cd frontend
npm install
npm run dev
```
*Aplicación web disponible en: `http://localhost:3000`*

---

## 🧪 5. Quality Gate & Certificación de Calidad

El monorepo cuenta con un estricto pipeline de calidad de código y cobertura:

```bash
# Ejecutar suite de pruebas completa con reporte de cobertura
.venv/bin/pytest --cov=backend

# Validar formateo y directrices de arquitectura limpia
ruff check backend/
mypy backend/src/
```

### Resultados de la Certificación Quality Gate (Paso 7)
* **308 pruebas unitarias, de integración y E2E aprobadas** (`100% Passing`).
* **Cobertura global de backend:** `87%` en módulos de producción.
* **Cero dependencias circulares:** Dominio fisiológico (`backend/src/domain`) 100% desacoplado de frameworks e infraestructura.
* **Tolerancia a fallos:** Ingesta resiliente de archivos con CRC-16 estricto, mitigación de picos de altitud barométrica y protección con SHA-256 contra duplicados.

---

## 📡 6. Catálogo de Endpoints de la API (FastAPI v1)

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Registro de atleta y creación de perfil basal |
| `POST` | `/api/v1/auth/login` | Autenticación y generación de par de tokens JWT |
| `POST` | `/api/v1/activities/upload` | Carga multipart asíncrona de archivos `.FIT`, `.GPX` y `.CSV` (Retorna HTTP 202 con `job_id`) |
| `GET` | `/api/v1/activities/jobs/{id}` | Sondeo de estado del procesamiento de telemetría |
| `GET` | `/api/v1/activities/` | Listado paginado de actividades del atleta autenticado |
| `GET` | `/api/v1/diagnostics/physiological-readiness` | Curvas de Fitness ($CTL$), Fatiga ($ATL$), Forma ($TSB$) y ratio $ACWR$ |
| `POST` | `/api/v1/goals/` | Creación de objetivo deportivo (asfalto, trail vertical o trekking) |
| `GET` | `/api/v1/plans/current` | Plan de entrenamiento periodizado con microciclos adaptativos |

---

## ⚖️ 7. Licencia y Créditos

**Páramo Urbano (v2.0.0 Core)** es propiedad exclusiva de ingeniería interna.  
Diseñado y desarrollado con rigor de alta montaña para atletas que transforman el asfalto en sendero y la altitud en su mayor fortaleza.
