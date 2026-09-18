# ADR-002: Esquema Canónico de Telemetría y Normalización Multi-Formato

## Estado
Aprobado (Accepted) — 2026-09-18

## Contexto
Páramo Urbano (v2.0.0 Core) ingesta archivos de telemetría deportiva provenientes de múltiples fabricantes (Garmin, Polar, Strava, Suunto, Coros) en formatos heterogéneos: binario FIT (SDK v21), GPX (XML con elevación 3D y extensiones de FC) y exportaciones CSV (delimitadas por coma o punto y coma con encabezados bilingües).

El motor de periodización y las analíticas fisiológicas no deben acoplarse a las estructuras particulares de cada fabricante ni a las inconsistencias de muestreo y sensores espurios.

## Decisión
1. **Contrato Canónico Único (`CanonicalActivityRecord`):**
   - Normalizar todas las fuentes a un objeto inmutable de dominio que contiene: `record_id`, `sport_category`, `started_at`, `duration_seconds`, `distance_meters`, `elevation_gain_meters`, `avg_speed`, `max_speed`, `avg_hr`, `max_hr`, `file_hash` (SHA-256), `telemetry_points_count` y `hr_zones_distribution`.
2. **Sanitización Fisiológica Obligatoria:**
   - Todo punto de telemetría debe validarse contra límites biológicos estrictos: FC [30, 240] bpm, altitud [-500, 9000] m, velocidad [0.0, 12.5] m/s.
   - Microoscilaciones barométricas menores a 3.0 m son descartadas mediante histéresis antes de calcular la ganancia vertical (+D).
3. **Deduplicación Criptográfica:**
   - La unicidad de la carga de archivos se garantiza mediante el cálculo previo del digest SHA-256 sobre el buffer binario crudo original (`file_hash_sha256`), bloqueando reingestas redundantes.

## Consecuencias
- **Positivas:** Desacoplamiento total del motor fisiológico respecto a vendors, protección contra inyecciones y cargas corruptas, reproducibilidad total en cálculos de carga.
- **Negativas:** Los metadatos propietarios no estándar de fabricantes específicos son descartados de la base de datos relacional y retenidos únicamente en el almacenamiento crudo de MinIO.
