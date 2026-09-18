# Changelog — Páramo Urbano

Todas las modificaciones notables de este proyecto serán documentadas en este archivo.

El formato se basa estrictamente en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/)
y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [2.1.0] - 2026-09-18

### Añadido (Added)
- **Asistente Outdoor Andino (P1 Andean Intelligence):**
  - Servicio de dominio y base de conocimiento técnico (`data/knowledge/destinos_andinos.json`) para cumbres ecuatorianas: Cotopaxi, Chimborazo, Cayambe, Rucu Pichincha, El Corazón e Illiniza Norte.
  - Pautas de aclimatación determinista, prevención de hipoxia y detección de Mal Agudo de Montaña (MAM).
  - Protocolo de escalamiento de emergencia médica y contratación de guías ASEGUIM/UIAGM vía enlace directo a WhatsApp.
  - Componente de interfaz de usuario flotante (`ChatbotAssistant.tsx`) con chips de consulta rápida, tarjetas de destinos y diálogos interactivos accesibles (WAI-ARIA).
  - Endpoints REST `/api/v1/assistant/chat` y `/api/v1/assistant/destinations`.
- **Carga Masiva de Actividades Manuales (Batch Logging):**
  - Caso de uso `batch_log_manual_activities` y DTOs de validación `BatchManualActivityRequestDTO`.
  - Soporte para registro por lotes vía API REST y modal interactivo con importación/exportación JSON.
- **Canalizaciones de Integración Continua (CI/CD Pipelines):**
  - Flujo GitHub Actions de backend (`.github/workflows/ci-backend.yml`): Flake8, Black, Mypy, Pytest con 100% cobertura fisiológica e idempotencia de seeds.
  - Flujo GitHub Actions de frontend (`.github/workflows/ci-frontend.yml`): TypeScript compilation (`tsc --noEmit`), ESLint, Vitest y bundle Vite.
  - Flujo unificado de Quality Gates (`.github/workflows/quality-gates.yml`): Certificación de 5 etapas NFR.
- **Despliegue y Orquestación de Infraestructura (DevOps):**
  - Dockerfiles multi-etapa para Backend (`backend/Dockerfile`) y Frontend (`frontend/Dockerfile` sobre Alpine Nginx).
  - Compose de Staging (`infra/docker/docker-compose.staging.yml`) con Nginx reverse proxy y límites de subida de telemetría.
  - Script de validación de humo para staging (`infra/scripts/smoke_test_staging.sh`).
  - Suite de utilidades operativas en `scripts/`: `manage.sh`, `start.sh`, `stop.sh`, `status.sh`, `restart.sh`, `reset_db.sh` y `start_tunnel.sh`.
- **Ejecutor de Pruebas Frontend Determinista:**
  - Script `frontend/test.mjs` para ejecución programática de Vitest con aislamiento in-memory, eliminando bloqueos de esbuild en entornos no interactivos.

### Modificado (Changed)
- Actualización de versión del sistema a **v2.1.0** en `pyproject.toml`, FastAPI Core (`main.py`), endpoint `/health`, frontend `package.json` y `docs/DEPLOYMENT_GUIDE.md`.
- Refactorización de `DiagnosticsView.tsx` y `PlannerView.tsx` en estricto cumplimiento con **ADR-006** (ancho máximo centrado a 680px y eliminación de tarjetas no aplicables).
- Persistencia políglota con fallback transparente a SQLite local (`paramo_urbano_dev.db`) en caso de indisponibilidad de PostgreSQL para agilizar el desarrollo local sin dependencias pesadas.
- Actualización de `README.md` con las nuevas insignias de calidad, total de 349 pruebas automatizadas y documentación de nuevas capacidades.

### Corregido (Fixed)
- Polyfill de `Element.prototype.scrollIntoView` en jsdom (`frontend/tests/setup.ts`) para estabilizar las pruebas de renderizado del asistente.
- Limpieza de variables no utilizadas en analizador de telemetría CSV (`csv_matcher.py`).
- Ajuste de longitud de líneas en `andean_assistant_service.py` y DTOs para cumplir con el límite estricto de 120 caracteres en Flake8 y Black.
- Corrección de advertencias de ESLint en componentes React.

---

## [2.0.0-core] - 2026-09-18

### Añadido (Added)
- **Motor Fisiológico Determinista (Core Domain):**
  - Algoritmo Banister Impulse-Response EWMA para cálculo de CTL (Fitness, $\tau_1=42$ días), ATL (Fatiga, $\tau_2=7$ días) y TSB (Balance).
  - Modelo ACWR de Gabbett con sweet spot (0.8 - 1.3) y regla estricta de descanso forzoso (ACWR > 1.5).
  - Cuantificación de carga Session-RPE de Foster (sRPE = Duración [min] $\times$ RPE [1-10]).
  - Algoritmo VDOT de Jack Daniels con corrección hipóxica por altitud barométrica.
- **Pipeline de Ingestión y Parsers Canónicos:**
  - Soporte de archivos `.FIT` binarios (Garmin/Wahoo) con validación de magic bytes y CRC-16.
  - Soporte de archivos `.GPX` XML con protección activa contra inyección XXE.
  - Soporte de archivos `.CSV` multiformato (Strava, Polar, Garmin) con detección heurística de columnas.
- **Clean Architecture Backend (Python 3.11 + FastAPI):**
  - Entidades de dominio, Value Objects inmutables, repositorios desacoplados con SQLAlchemy 2.0 y asyncpg.
  - Cola asíncrona de ingestión con Redis (`RedisJobQueue`) y almacenamiento de objetos S3 con MinIO.
  - Filtro de privacidad geográfica (ofuscación por radio de 500 metros en puntos de partida/llegada).
- **Frontend SPA (React 18 + TypeScript + Vite):**
  - Vistas de diagnóstico fisiológico, subida dropzone de telemetría, visor de calendario y periodización.
- **Garantía de Calidad:**
  - 100% de cobertura de código en el núcleo fisiológico (`backend.src.domain.physiological`).
  - Suite de criterios de aceptación E2E en Gherkin (FR-01 a FR-05 y NFRs).
