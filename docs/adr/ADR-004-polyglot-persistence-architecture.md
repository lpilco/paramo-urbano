# ADR-004: Persistencia Políglota (PostgreSQL 16 + MinIO / S3 + Redis)

## Estado
Aprobado (Accepted) — 2026-09-18

## Contexto
El flujo de telemetría deportiva e ingesta masiva en Páramo Urbano impone requerimientos divergentes de almacenamiento:
1. Las series temporales crudas binarias (.FIT, .GPX, .CSV) son inmutables, voluminosas (hasta 25 MB por archivo) y de lectura esporádica (re-parseo o exportación).
2. Los modelos relacionales (perfiles de atletas, metas, actividades agregadas, resúmenes biométricos, microciclos y planes) exigen integridad transaccional ACID, claves foráneas, restricciones de rango e indexación relacional compleja.
3. La ingesta de archivos no debe bloquear el hilo principal de la API web; el cliente debe recibir una respuesta inmediata HTTP 202 Accepted con `job_id` mientras el cómputo pesado ocurre en un proceso worker desacoplado.

## Decisión
Adoptar una arquitectura de persistencia políglota distribuida en tres capas especializadas:

1. **Almacenamiento de Objetos Crudos (MinIO / S3 Compatible):**
   - Bucket inmutable: `paramo-raw-telemetry`.
   - Llaves estructuradas: `{athlete_profile_id}/{sha256_hash}.{ext}`.
   - Conserva los bytes originales de la carga para auditoría o re-procesamiento.
2. **Base de Datos Relacional Transaccional (PostgreSQL 16):**
   - Modelo relacional normalizado para usuarios, perfiles, metas, actividades, resúmenes agregados (`activity_telemetry_summary`), jobs de ingesta y periodización.
   - Campos agregados en columnas nativas e histogramas de zonas cardíacas y de ritmo en columnas `JSONB`.
   - Integridad criptográfica garantizada por índice único sobre `file_hash_sha256`.
3. **Cola de Mensajería y Coordinación Asíncrona (Redis):**
   - Estructura de cola para jobs pendientes con payload `(job_id, athlete_profile_id, file_storage_key, file_hash_sha256)`.
   - Worker independiente que consume la cola, recupera el blob de MinIO, ejecuta `ParseActivityFileUseCase`, actualiza basales fisiológicos (Banister EWMA y ACWR) y persiste la actividad atómicamente.

## Consecuencias
- **Positivas:** Máximo rendimiento I/O en la API REST, aislamiento total de fallos de parseo sin comprometer la disponibilidad del servicio web, base de datos relacional compacta y ágil, escalabilidad elástica horizontal de workers.
- **Negativas:** Requiere orquestar múltiples servicios de infraestructura (PostgreSQL, MinIO, Redis) y gestionar estados de consistencia eventual a través de la entidad `ingestion_jobs`.
