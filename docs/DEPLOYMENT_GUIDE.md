# Guía Operativa de Despliegue y Certificación Staging / Producción
## Páramo Urbano (v2.0.0 Core) — "Donde el asfalto toca la cumbre"

---

## 1. Visión General y Alcance

Este documento describe la arquitectura operativa, la matriz de secretos, los procedimientos de despliegue continuo (CD), las políticas de rollback automatizado y las pruebas de humo (*smoke testing*) para **Páramo Urbano (v2.0.0 Core)**.

El entorno de **Staging** está dimensionado y configurado específicamente para soportar la **Fase 2: Beta Técnica** (semanas 5 a 8, 100 atletas andinos: 40 de asfalto, 40 de trail running y 20 de senderismo/hike), certificando los requerimientos no funcionales (NFRs) definidos en el PRD:
* **NFR-01:** Latencia de respuesta en ingesta $\le 250\text{ ms}$ (HTTP 202 Accepted con `job_id`).
* **NFR-02:** Rendimiento del worker de decodificación $\le 1.8\text{ s}$ para 2 horas de telemetría a 1 Hz (~7.200 registros).
* **NFR-03:** Ofuscación geográfica de radio de privacidad de 500 metros en coordenadas residenciales.
* **NFR-04:** Seguridad de aplicación (mitigación XXE en GPX, magic bytes en FIT, tokens RSA-256 JWT y Argon2).

---

## 2. Diagrama de Arquitectura de Despliegue (Staging)

```mermaid
graph TD
    subgraph Internet / Clientes
        Atleta["Atleta Andino (Navegador / Wearable)"]
    end

    subgraph "Host / VPS Staging (Docker Network: paramo_staging_network)"
        NginxFrontend["Frontend Nginx (Puerto 80/3000)<br/>SPA Router + Security Headers + Gzip"]
        FastAPIGateway["Backend API FastAPI (Puerto 8000)<br/>Non-root:nonroot (1.5 CPU / 1GB RAM)"]
        WorkerService["Telemetry Worker Desacoplado<br/>Non-root:nonroot (1.0 CPU / 1GB RAM)"]
        
        PostgresDB[("PostgreSQL 16 Alpine<br/>(1.0 CPU / 1GB RAM)<br/>Volume: staging_postgres_data")]
        RedisQueue[("Redis 7 Alpine (Cola AOF)<br/>(0.5 CPU / 512MB RAM)<br/>Volume: staging_redis_data")]
        MinIOStore[("MinIO S3 Compatible<br/>(0.5 CPU / 512MB RAM)<br/>Volume: staging_minio_data")]
    end

    Atleta -->|"HTTPS / HTTP GET /"| NginxFrontend
    Atleta -->|"REST API /api/v1/*"| NginxFrontend
    NginxFrontend -->|"Reverse Proxy /api/*"| FastAPIGateway
    FastAPIGateway -->|"SQLAlchemy Async (asyncpg)"| PostgresDB
    FastAPIGateway -->|"Ingest Job Enqueue"| RedisQueue
    FastAPIGateway -->|"Raw Binaries Upload"| MinIOStore
    WorkerService -->|"BRPOP Job Dequeue"| RedisQueue
    WorkerService -->|"Download Binary .FIT/.GPX"| MinIOStore
    WorkerService -->|"Persist Normalized Telemetry"| PostgresDB
```

---

## 3. Matriz de Secretos Requeridos (GitHub Repository Secrets)

Para habilitar la Integración Continua (CI) y el Despliegue Continuo (CD), configure las siguientes variables en **GitHub Repository Settings > Secrets and variables > Actions**:

| Nombre del Secreto | Tipo / Formato | Propósito Operativo | Entornos Requeridos |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | URI (`postgresql://user:pass@host:5432/db`) | Cadena de conexión asíncrona a PostgreSQL | CI, Staging, Producción |
| `DB_USER` | String alfanumérico | Usuario propietario de la base de datos | Staging, Producción |
| `DB_PASSWORD` | Passphrase segura ($\ge 24$ chars) | Contraseña de acceso transaccional | Staging, Producción |
| `DB_NAME` | String identificador (`paramo_db`) | Nombre de la base de datos operativa | Staging, Producción |
| `REDIS_PASSWORD` | Passphrase segura ($\ge 24$ chars) | Clave de autenticación Redis AUTH | Staging, Producción |
| `MINIO_ROOT_USER` | String identificador | Credencial administrativa de MinIO | Staging, Producción |
| `MINIO_ROOT_PASSWORD` | Passphrase segura ($\ge 24$ chars) | Clave de acceso administrativa MinIO | Staging, Producción |
| `JWT_PRIVATE_KEY_PEM` | PEM format (`-----BEGIN PRIVATE KEY...`) | Llave privada RSA-2048 para firma de tokens JWT | Staging, Producción |
| `JWT_PUBLIC_KEY_PEM` | PEM format (`-----BEGIN PUBLIC KEY...`) | Llave pública RSA-2048 para verificación JWT | Staging, Producción |
| `STAGING_HOST` | IPv4 / FQDN (`staging.paramourbano.io`) | Dirección del servidor o VPS de Staging | CD Pipeline |
| `STAGING_USER` | String (`deployer` o `ubuntu`) | Usuario Linux con privilegios Docker | CD Pipeline |
| `STAGING_SSH_KEY` | OpenSSH Private Key | Llave SSH para conexión automatizada sin password | CD Pipeline |

> [!CAUTION]
> Nunca almacene llaves privadas ni contraseñas en texto plano dentro del repositorio ni en archivos `.env` versionados en Git. Utilice siempre variables inyectadas mediante el gestor de secretos de la plataforma o de GitHub.

---

## 4. Procedimiento de Despliegue Continuo (Staging / VPS)

### 4.1 Preparación Inicial del Host (One-Time Setup)

En el servidor destino (Ubuntu 22.04 LTS / 24.04 LTS recomendado):

```bash
# 1. Actualizar sistema e instalar Docker Engine + Docker Compose Plugin
sudo apt-get update && sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# 2. Agregar usuario deployer al grupo docker
sudo usermod -aG docker $USER

# 3. Crear directorio base de despliegue
sudo mkdir -p /opt/paramo-urbano && sudo chown -R $USER:$USER /opt/paramo-urbano
```

### 4.2 Despliegue Automatizado con Docker Compose

Desde el pipeline de CD o manualmente vía SSH en `/opt/paramo-urbano`:

```bash
# 1. Clonar o actualizar el repositorio en la rama staging
git fetch origin staging && git checkout staging && git pull origin staging

# 2. Inyectar secretos en el archivo de entorno .env de staging
cat <<EOF > .env
NODE_ENV=staging
APP_NAME="Paramo Urbano Core (Staging)"
APP_VERSION=2.1.0
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
REDIS_PASSWORD=${REDIS_PASSWORD}
MINIO_ROOT_USER=${MINIO_ROOT_USER}
MINIO_ROOT_PASSWORD=${MINIO_ROOT_PASSWORD}
JWT_SECRET=${JWT_SECRET}
STORAGE_BUCKET_RAW_ACTIVITIES=paramo-raw-telemetry
MAX_UPLOAD_FILE_SIZE_BYTES=26214400
EOF

# 3. Desplegar los servicios con reconstrucción de imágenes y límites de recursos
docker compose -f infra/docker/docker-compose.staging.yml up --build -d

# 4. Verificar salud de los contenedores
docker compose -f infra/docker/docker-compose.staging.yml ps
```

---

## 5. Protocolo de Rollback Automatizado

Si tras el despliegue el healthcheck falla o las pruebas de humo reportan anomalías, ejecute el rollback inmediato para restaurar la versión estable previa:

```bash
#!/usr/bin/env bash
set -e

echo "[ROLLBACK] Iniciando procedimiento de contingencia..."

# 1. Guardar logs para análisis forense post-mortem
docker compose -f infra/docker/docker-compose.staging.yml logs --tail=500 > /var/log/paramo_rollback_$(date +%s).log

# 2. Revertir al commit o tag previo etiquetado como estable
git checkout HEAD~1

# 3. Re-desplegar versión previa de forma forzada
docker compose -f infra/docker/docker-compose.staging.yml up --build -d

# 4. Esperar estabilización y certificar con smoke test
sleep 15
./infra/scripts/smoke_test_staging.sh "http://localhost" "http://localhost:8000"

echo "[ROLLBACK] Rollback completado con éxito. Sistema restaurado a versión previa."
```

---

## 6. Pruebas de Humo (Smoke Tests) y Certificación de NFRs

Para validar la operatividad del sistema inmediatamente después de un despliegue, ejecute:

```bash
./infra/scripts/smoke_test_staging.sh "http://localhost:3000" "http://localhost:8000"
```

El script evalúa de forma automatizada:
1. **Frontend SPA:** Disponibilidad HTTP 200 y renderizado del shell HTML.
2. **API Gateway Health:** Respuesta de `/health` en menos de 250 ms.
3. **Flujo de Autenticación:** Registro o token mock de atleta.
4. **NFR-01 (Fast Ingestion):** Subida asíncrona de archivo de telemetría respondiendo HTTP 202 con `job_id` en $\le 250\text{ ms}$.
5. **NFR-02 (Worker Throughput):** Confirmación de procesamiento y cambio de estado del job en el worker desacoplado.

---

## 7. Runbooks de Operación y Mantenimiento

### 7.1 Migraciones y Seeding de Datos
Para inicializar o re-sembrar datos idempotentes (ej. usuarios demo de asfalto y senderismo para el cohorte):
```bash
docker compose -f infra/docker/docker-compose.staging.yml exec backend_api python -m backend.src.infrastructure.database.seeds
```

### 7.2 Inspección de Cola Redis y Worker
Para consultar la longitud de la cola de ingestión y el estado de procesamiento:
```bash
# Longitud de la cola de telemetría pendiente
docker compose -f infra/docker/docker-compose.staging.yml exec redis redis-cli -a "$REDIS_PASSWORD" LLEN paramo:queue:telemetry_ingestion

# Logs en tiempo real del worker
docker compose -f infra/docker/docker-compose.staging.yml logs -f backend_worker
```

### 7.3 Respaldo de Base de Datos PostgreSQL
```bash
docker compose -f infra/docker/docker-compose.staging.yml exec -T postgres pg_dump -U paramo_admin paramo_db | gzip > /backups/paramo_backup_$(date +%Y%m%d_%H%M%S).sql.gz
```
