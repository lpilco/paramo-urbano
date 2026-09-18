# PRD — PÁRAMO URBANO (v2.0.0 Core)
## Documento de Requerimientos de Producto & Especificación de Arquitectura Técnica

* **Producto:** Páramo Urbano (v2.0.0 Core).
* **Tagline:** *«Donde el asfalto toca la cumbre»*.
* **Descriptores Técnicos:** *Páramo Urbano: Asfalto, Trail & Altitud* | *Telemetría y periodización inteligente para atletas de montaña y ciudad*.
* **Estado:** Aprobado para Implementación Técnica y Construcción (Ready for Engineering).
* **Público Objetivo:** Corredores Urbanos de Asfalto, Trail Runners y Senderistas / Montañistas Andinos.
* **Nivel de Confidencialidad:** Propiedad exclusiva de ingeniería interna.

---

### 1. Visión del Producto, Propósito y Métricas de Negocio

#### 1.1 Declaración del Problema
El deportista andino contemporáneo enfrenta una fragmentación operativa y tecnológica crítica:
* **Trackers masivos convencionales (Strava, Nike Run Club):** Operan como redes sociales de logging pasivo; carecen de modelado de fatiga biológica, no previenen el sobreentrenamiento ni calculan el impacto del desnivel pronunciado.
* **Plataformas analíticas tradicionales (TrainingPeaks, WKO5):** Imponen costos prohibitivos, interfaces complejas y dependen de supervisión de entrenadores humanos.
* **Apps adaptativas de running (Runna, V.O2):** Están sesgadas exclusivamente hacia el asfalto plano mediante VDOT o ritmos fijos, ignorando la altitud, el terreno técnico y el desnivel acumulado (+D).

#### 1.2 Propuesta de Valor y Plataforma Estratégica
* **Propósito:** Tender un puente de ciencia y telemetría entre la disciplina del concreto y la inmensidad de la cumbre, transformando la altitud andina en el mayor activo de rendimiento del atleta.
* **Misión:** Democratizar la periodización determinista y la monitorización biomecánica para atletas híbridos, sincronizando asfalto, senderos técnicos y desniveles acumulados para evitar lesiones.
* **Visión:** Consolidarse como la plataforma tecnológica SportTech de referencia en América Latina, liderando el modelado de carga en altitud y redefiniendo el running de altura.
* **Categoría de Producto:** Urban Trail y Alpinismo de Base Científica.

#### 1.3 Valores Inmutables de Ingeniería y Producto
* **Rigor Determinista (Sin Conjeturas):** Queda estrictamente prohibido delegar el cálculo de carga, fatiga o prescripción a modelos estocásticos (LLMs). Todo cómputo se rige por formulaciones matemáticas auditables (Banister, Foster, Gabbett, Daniels).
* **Resiliencia Híbrida:** Cuantificación equivalente del impacto articular en pavimento rígido y del desgaste excéntrico en descensos técnicos de montaña.
* **Arraigo Territorial Andino:** Modelado específico para adaptación a la hipoxia y pisos altitudinales andinos.
* **Seguridad Biomecánica Prioritaria:** Control estricto de ratios lesivos (ACWR) con inyección obligatoria de días de descanso.

#### 1.4 Métricas de Éxito del Producto (KPIs)
* **Retención D30:** $\ge 42\%$ de retención de atletas activos al día 30 post-onboarding.
* **Ratio de Ingesta Exitosa:** $\ge 99.2\%$ de archivos (.FIT, .GPX, .CSV, .JSON) procesados asíncronamente sin errores no recuperables.
* **Workout Completion Rate (WCR):** $\ge 68\%$ de sesiones planificadas completadas o emparejadas con telemetría.
* **Engagement Ratio (DAU/MAU):** $\ge 0.35$, dinamizado por el check-in diario de recuperación y consulta del planificador.
* **Reducción de Lesiones Autodeclaradas:** Reducción del $25\%$ frente al estándar recreativo mediante alertas de $ACWR > 1.3$.

---

### 2. Arquetipos de Usuario y User Journeys (Onboarding Bifurcado)

```text
                       [ SCREENING INICIAL ]
                                 |
        +------------------------+------------------------+
        |                                                 |
  [ PERFIL A: AVANZADO ]                           [ PERFIL B: PRINCIPIANTE ]
        |                                                 |
  Dropzone Asíncrono                               Cuestionario guiado
  Archivos .FIT / .GPX / .CSV                      (Edad, Peso, Días)
        |                                                 |
  Hash SHA-256 + Deduplicación                     Perfil Basal Gellish
  Worker decodifica a Canonical                    Método CaCo y Foster sRPE
        |                                                 |
  Cálculo Banister Retrospectivo                   Empty State Didáctico
  (CTL ~58, ATL ~49, TSB ~+9)                      Registro manual en 30s
        |                                                 |
        +------------------------+------------------------+
                                 |
                     [ SELECTOR DE META ]
         (Asfalto km / Trail D+ / Trekking Pisos)
                                 |
                 [ PLANIFICADOR PERIODIZADO ]
               (Vistas: Diario / Semanal / Mensual)
```

#### 2.1 Perfil A: Atleta Híbrido / Avanzado (Con Historial)

* **Demografía:** 28 a 48 años; entrena de 4 a 6 días por semana combinando asfalto y senderos.
* **Equipamiento:** Reloj GPS multideporte (Garmin, Suunto, Polar, Coros), pulsómetro pectoral.
* **User Journey:**
  1. **Screening:** Selecciona «Tengo historial de entrenamientos / Archivos GPS».
  2. **Ingesta Masiva:** Arrastra un lote de archivos (.FIT, .GPX, .CSV) de hasta 25 MB por archivo.
  3. **Procesamiento Asíncrono:** API retorna HTTP 202 con `job_id`; workers validan SHA-256 y parsean en segundo plano.
  4. **Línea Base Fisiológica:** El motor Banister genera curvas retrospectivas de Fitness ($CTL \approx 58$), Fatiga ($ATL \approx 49$) y Forma ($TSB \approx +9$) en ventana móvil de 42 días.
  5. **Meta:** Configura competencia (ej. Maratón de Montaña 42 km con 2.400 m D+ a 14 semanas).
  6. **Plan:** Despliegue de microciclos que balancean series en calle y volumen vertical en montaña.

#### 2.2 Perfil B: Atleta Debutante / Iniciación y Senderismo

* **Demografía:** 20 a 55 años; busca iniciarse en el running, preparar sus primeros 5 km o realizar caminatas de media montaña.
* **Equipamiento:** Smartphone o reloj básico; sin sensores de frecuencia cardíaca avanzados.
* **User Journey:**
  1. **Screening:** Selecciona «Comienzo desde cero / Sin archivos de telemetría».
  2. **Cuestionario:** Declara edad, peso, disponibilidad semanal y meta inicial.
  3. **Perfil Fisiológico Basal:** Cálculo de $FC_{\text{máx}}$ teórica mediante Gellish: $208 - (0.7 \times \text{edad})$.
  4. **Empty State Didáctico:** Panel de bienvenida con directrices del método Caminar/Correr (CaCo) y escala Foster sRPE (1-10).
  5. **Primer Registro:** Completa su primera sesión de CaCo y la registra manualmente en 30 segundos (ej. 30 min a RPE 4).
  6. **Cómputo Adaptativo:** El sistema deduce 120 u.a. de carga y prescribe pautas de hidratación y movilidad.

---

### 3. Arquitectura Modular del Sistema (Core Modules)

#### 3.1 Módulo de Ingesta y Telemetría (Ingestion Engine)

* **Upload Handler Asíncrono:** Endpoint multipart para cargas de hasta 25 MB por archivo. Genera un hash SHA-256 del binario para rechazo inmediato de duplicados. Retorna HTTP 202 Accepted con `job_id`.
* **Decodificador Binario FIT:** Basado en FIT SDK v21.x. Valida en bytes 8-11 la firma ASCII .FIT (`0x2E 0x46 0x49 0x54`) y ejecuta comprobación de integridad CRC-16. Extrae mensajes `file_id`, `session` y `record` (1 Hz). Tolera e ignora campos propietarios (`developer_data_id`) sin interrumpir la ejecución.
* **Parser XML GPX:** Extrae tridimensionalidad (lat, lon, ele) y marcas UTC. Incluye defensas activas contra inyecciones XML External Entity (XXE).
* **Heuristic CSV Matcher:** Normaliza exportaciones heterogéneas de Strava, Garmin Connect y Polar mapeando columnas a los atributos del sistema.
* **Sanitizador Fisiológico:** Descarte estricto de anomalías de hardware:
  * Frecuencia cardíaca: $30\text{ bpm} \le HR \le 240\text{ bpm}$.
  * Altitud barométrica: $-500\text{ m} \le \text{Altitud} \le 9.000\text{ m}$.
  * Velocidad: $0\text{ m/s} \le \text{Velocidad} \le 12.5\text{ m/s (45 km/h)}$.
  * Filtro barométrico de montaña: Histéresis de 3 metros para descartar oscilaciones espurias.
* **Canonical Activity Normalizer:** Convierte cualquier entrada al esquema tipado unificado `CanonicalActivityRecord`.

#### 3.2 Módulo de Diagnóstico y Métricas Fisiológicas (Workload & Analytics Engine)

* **Cuantificación de Carga:**
  * Sesiones con FC/Potencia: Cálculo de hrTSS / rTSS.
  * Sesiones manuales sin sensor (Foster sRPE): $\text{Carga} = \text{Duración (minutos)} \times \text{RPE (escala 1 a 10)}$.
* **Modelo Banister de Respuesta al Impulso (EWMA):**
  * Fitness Crónico (CTL): $\tau_1 = 42\text{ días}$.
  * Fatiga Aguda (ATL): $\tau_2 = 7\text{ días}$.
  * Balance de Estrés / Forma (TSB): $TSB = CTL - ATL$.
* **Control Lesivo (ACWR de Gabbett):** Relación entre carga aguda de 7 días y crónica de 28 días.
  * Sweet Spot: $0.8 \le ACWR \le 1.3$ (Adaptación aeróbica óptima).
  * Zona de Precaución: $1.3 < ACWR \le 1.5$ (Congelamiento de incrementos de volumen).
  * Zona Crítica Lesiva: $ACWR > 1.5$ (Gatillo automático de descanso obligatorio).

#### 3.3 Módulo de Planificación y Periodización (Planner Engine)

* **Regla de Progresión Segura:** Prohibido incrementar el volumen o carga semanal en más de un 10% respecto a la semana previa.
* **Descarga Estructurada:** Cada 3 semanas de sobrecarga progresiva (Build), se intercala 1 semana de descarga regenerativa (Recovery) con reducción de volumen del 30–40% manteniendo la intensidad neuromuscular.
* **Fase de Puesta a Punto (Tapering):** Reducción progresiva de volumen en los últimos 10 a 14 días previos a la meta para alcanzar un TSB positivo (+5 a +15) el día del evento.
* **Segmentación Territorial:**
  * **Asfalto:** Parciales de ritmo (min/km), cadencia y zonas de frecuencia cardíaca.
  * **Trail Running:** Desnivel positivo acumulado (+D), velocidad vertical de ascenso (VAM en m/h) y fuerza excéntrica en descenso.
  * **Trekking:** Volumen horario sostenido, aclimatación por pisos altitudinales y control de carga con mochila.

#### 3.4 Módulo de Perfil, Recuperación y Auditoría (Profile & Recovery Engine)

* **Check-in Diario de Recuperación:** Captura subjetiva de calidad de sueño, dolor muscular (Escala Hooper 1 a 5), estrés y cómputo de Readiness Score (0% a 100%).
* **Prescripción Contextual de Nutrición:**
  * Sesiones de Fuerza/Neuromuscular: Aporte proteico prioritario (1.8 a 2.2 g/kg/día).
  * Largadas y Montaña: Sobrecarga glucogénica (6 a 8 g/kg/día), hidratación isotónica con reposición de sodio (500–750 ml/h).
  * Días de Descanso: Pauta normocalórica con antioxidantes y magnesio.
* **Prescripción de Terapias Físicas de Descarga:**
  * Sesiones de Fuerza: Sauna seco (15–20 min a 80°C) y automasaje con foam roller.
  * Largadas / Desniveles: Hidroterapia de contraste (3 ciclos de 1 min frío a 12°C por 3 min caliente a 38°C) y masaje de descarga deportiva.

---

### 4. Alcance del MVP: In-Scope vs. Out-of-Scope

| Dimensión | In-Scope (Lanzamiento MVP v2.0) | Out-of-Scope (Fase 2 / Backlog Futuro) |
| :--- | :--- | :--- |
| **Plataforma** | Aplicación Web responsiva (PWA para Desktop, Tablet y Mobile). | Aplicaciones móviles nativas en Swift (iOS) o Kotlin (Android). |
| **Ingesta de Datos** | Carga asíncrona de archivos .FIT, .GPX, .CSV y .JSON con hash SHA-256. Formulario manual sRPE. | Sincronización nube-a-nube desasistida vía OAuth (Garmin Connect, Strava API). |
| **Hardware** | Decodificación de archivos exportados desde cualquier wearable ANT+/GPS. | Despliegue directo a Apple WorkoutKit o Garmin Training API en el reloj. |
| **Catálogo de Metas** | Asfalto (5K a Ultra con km exactos), Trail (+D y km obligatorios) y Trekking (pisos altitudinales). | Planes de Triatlón (Ironman) o Alpinismo técnico vertical de alta dificultad. |
| **Motor Fisiológico** | Modelo Banister (CTL/ATL/TSB), semáforo ACWR de Gabbett y descansos forzados. | Modelado biomecánico tridimensional de zancada por visión artificial. |
| **Periodización** | Planificador periodizado adaptativo con vistas Diaria, Semanal y Mensual. | Replanificación meteorológica automatizada ante tormentas en tiempo real. |
| **Comunidad** | Perfil de usuario individual centrado en telemetría y salud. | Feed social público, muros, comentarios o tablas de clasificación. |
| **Monetización** | Acceso de evaluación y validación técnica del producto. | Pasarelas de facturación recurrente multidivisa (Stripe / PayPal). |

---

### 5. Requerimientos Funcionales (FR) y Criterios de Aceptación (Gherkin)

#### FR-01: Registro e Importación Masiva de Sesiones Pasadas

* **Historia de Usuario:** Como atleta experimentado con historial en dispositivos GPS, quiero subir de forma masiva mis archivos .FIT, .GPX o .CSV para que la plataforma calcule automáticamente mi estado fisiológico basal sin registros manuales tediosos.
* **Validación INVEST:** Independiente, Negociable, Valiosa, Estimable, Pequeña, Testeable.

```gherkin
Scenario: Carga exitosa por lotes de archivos .FIT y .GPX con deduplicación criptográfica
  Given que el atleta se encuentra autenticado en "/diagnostics"
  And selecciona 5 archivos válidos que suman 18 MB en total
  When suelta los archivos en el contenedor de carga asíncrona
  Then el sistema valida que ningún archivo exceda el límite de 25 MB
  And calcula el hash SHA-256 de cada archivo asegurando que no existan previamente en la base de datos
  And retorna un código HTTP 202 Accepted con identificadores de trabajo "job_id"
  And el worker procesa en segundo plano las métricas de distancia, elevación y pulso
  And la interfaz actualiza el panel marcando las actividades en estado PROCESSED.

Scenario: Rechazo de archivo binario .FIT corrupto o con cabecera alterada
  Given que un usuario intenta subir un archivo "actividad_corrupta.fit"
  When el parser de telemetría examina los bytes 8 al 11 del archivo
  And comprueba que no contienen la firma ASCII ".FIT" (0x2E 0x46 0x49 0x54)
  Then el sistema rechaza el archivo con código HTTP 422 Unprocessable Entity
  And marca la tarea con estado FAILED notificando el motivo técnico al usuario.
```

#### FR-02: Creación y Logging de Nueva Actividad Manual (Foster sRPE)

* **Historia de Usuario:** Como atleta que finalizó un entrenamiento de fuerza o un trote sin reloj GPS, quiero registrar manualmente la duración y el esfuerzo percibido (RPE 1-10) para mantener actualizada mi carga de entrenamiento sin desajustes.

```gherkin
Scenario: Registro manual de sesión de fuerza funcional mediante sRPE
  Given que el atleta finalizó una sesión de gimnasio sin archivo de telemetría
  When abre el modal de registro manual en "/diagnostics"
  And selecciona el deporte "STRENGTH", fecha actual, duración de 50 minutos y RPE de 8
  And presiona el botón "Guardar Entrenamiento"
  Then el backend persiste la actividad con source_type "MANUAL"
  And calcula deterministamente una carga Foster de 400 unidades (50 * 8)
  And recalcula el volumen semanal y las curvas de fatiga (ATL) del atleta
  And retorna HTTP 201 Created con el ID de la actividad creada.

Scenario: Validación de rango en esfuerzo percibido fuera de cota
  Given que el usuario completa el formulario manual
  When ingresa un valor de RPE de 12
  Then la interfaz bloquea el envío del formulario
  And muestra el error: "El RPE debe ser un número entero comprendido entre 1 y 10".
```

#### FR-03: Segmentación Territorial: Montaña (+D) vs. Asfalto (Ritmo)

* **Historia de Usuario:** Como atleta interdisciplinario, quiero que el sistema analice las sesiones de trail running priorizando el desnivel positivo acumulado (+D) y las de ruta por ritmo medio por kilómetro para reflejar el desgaste real de cada terreno.

```gherkin
Scenario: Procesamiento de sesión de Trail Running priorizando metros verticales
  Given que se procesa un archivo con categoría "TRAIL_RUN"
  When el normalizador analiza las cotas de altitud filtrando variaciones espurias menores a 3 metros
  Then calcula con precisión el desnivel positivo acumulado (+D en metros)
  And prioriza en el dashboard la velocidad de ascenso (VAM m/h) y el tiempo total sobre el ritmo plano.

Scenario: Procesamiento de sesión de Asfalto con desglose métrico de ritmo
  Given que se procesa un archivo con categoría "ROAD_RUN"
  When el sistema extrae los parciales por kilómetro
  Then desglosa el ritmo medio de cada km y su correspondencia con las zonas de pulso
  And omite el desnivel vertical como métrica determinante de la carga de la sesión.
```

#### FR-04: Dashboard Interactivo de Carga Semanal y Fatiga

* **Historia de Usuario:** Como atleta en entrenamiento regular, quiero consultar en un panel consolidado mis curvas de Fitness (CTL), Fatiga (ATL), Forma (TSB) y el semáforo ACWR para conocer mi disponibilidad biomecánica objetiva.

```gherkin
Scenario: Visualización de estado óptimo de frescura en el Dashboard
  Given que el atleta tiene acumulado un CTL de 60 y un ATL de 48
  When consulta la vista en "/diagnostics"
  Then el sistema renderiza un TSB positivo de +12 (60 - 48)
  And el velocímetro ACWR se sitúa en 1.05 dentro del "Sweet Spot" verde
  And despliega el estado: "FRESCURA ÓPTIMA: Preparado para asimilar alta intensidad".

Scenario: Detección automática de sobrecarga aguda y descanso obligatorio
  Given que un atleta experimenta un pico de volumen que eleva su ACWR a 1.62
  When el sistema recalcula los valores de la semana en curso
  Then el indicador de ACWR pasa a color ROJO (Zona de Peligro Biomecánico)
  And el planificador sustituye automáticamente la siguiente sesión intensa por un DÍA DE DESCANSO OBLIGATORIO.
```

#### FR-05: Configuración de Meta con Margen Temporal Seguro

* **Historia de Usuario:** Como atleta que prepara un objetivo competitivo, quiero definir mi prueba, distancia exacta, desnivel y fecha límite garantizando un tiempo biológico de adaptación adecuado.

```gherkin
Scenario: Configuración exitosa de meta de Trail Running a 16 semanas
  Given que el atleta navega al formulario de metas en "/onboarding/goals"
  When selecciona la disciplina "TRAIL_RUNNING", submeta "TRAIL_MARATHON", 42 km y 2200 m D+
  And escoge una fecha de carrera ubicada a 16 semanas en el futuro con 5 días semanales de disponibilidad
  Then el sistema valida que la fecha sea superior a la fecha actual más 14 días
  And persiste la meta en la tabla "athlete_goals"
  And retorna HTTP 200 OK redirigiendo de inmediato al usuario al planificador "/planner".

Scenario: Intento de configuración con fecha en el pasado o con margen biológico insuficiente
  Given que el atleta intenta fijar su fecha de competencia
  When selecciona una fecha que ocurrió ayer o que está a sólo 5 días en el futuro
  Then el calendario bloquea la selección y el formulario no permite el envío
  And muestra el mensaje: "La fecha objetivo debe programarse con al menos 14 días de antelación para permitir una adaptación biológica mínima".
```

---

### 6. Requerimientos No Funcionales (NFR)

#### 6.1 Rendimiento y Tiempos de Respuesta
* **Latencia de Upload API:** Respuesta HTTP 202 Accepted con `job_id` en menos de $250\text{ ms}$ para cualquier archivo $\le 25\text{ MB}$.
* **Rendimiento de Decodificación:** El worker debe parsear y normalizar un archivo .FIT de 2 horas (aproximadamente 7.200 records a 1 Hz) en $\le 1.8\text{ segundos}$ en el percentil 95 (p95).
* **Latencia Frontend:** Renderizado inicial de vistas del dashboard y planificador en menos de $800\text{ ms}$ sobre conexiones estándar.

#### 6.2 Seguridad, Privacidad y Normativa
* **Cifrado en Reposo:** Datos biométricos y de salud almacenados mediante AES-256.
* **Ofuscación Geográfica:** Radio de privacidad configurable de 500 metros alrededor del punto de partida y llegada para proteger la privacidad residencial.
* **Autenticación:** Tokens JWT con expiración corta (15 minutos) y Refresh Tokens rotativos almacenados en cookies HttpOnly, Secure y SameSite=Strict.

#### 6.3 Escalabilidad, Disponibilidad y Resiliencia
* **Arquitectura de Persistencia:** PostgreSQL para datos relacionales estructurados y Object Storage (MinIO / S3) para archivos binarios crudos originales inmutables.
* **Aislamiento de Errores:** En una carga masiva por lotes, la corrupción de un archivo particular marca únicamente dicho registro como FAILED sin abortar el procesamiento de los demás archivos válidos.
* **Disponibilidad:** SLA objetivo del 99.9% en producción.

---

### 7. Arquitectura Técnica y Contratos de Datos

#### 7.1 Modelo Entidad-Relación (PostgreSQL)

```text
+-------------------+       +-----------------------+       +-------------------+
|      USERS        |       |   ATHLETE_PROFILES    |       |   ATHLETE_GOALS   |
+-------------------+       +-----------------------+       +-------------------+
| id (UUID PK)      |1     1| id (UUID PK)          |1     N| id (UUID PK)      |
| email (VARCHAR)   |<----->| user_id (UUID FK)     |<----->| profile_id (FK)   |
| password_hash     |       | experience_level      |       | discipline        |
| created_at        |       | rest_hr, max_hr       |       | target_distance_km|
+-------------------+       | weight_kg             |       | target_elev_gain_m|
                            +-----------------------+       | target_date       |
                                        |1                  +-------------------+
                                        |
                 +----------------------+----------------------+
                 |1                                           1|
                 v N                                           v N
+-----------------------------------+       +-----------------------------------+
|            ACTIVITIES             |       |          TRAINING_PLANS           |
+-----------------------------------+       +-----------------------------------+
| id (UUID PK)                      |       | id (UUID PK)                      |
| athlete_profile_id (UUID FK)      |       | athlete_profile_id (UUID FK)      |
| source_type (FIT/GPX/CSV/MANUAL)  |       | goal_id (UUID FK)                 |
| file_hash_sha256 (VARCHAR)        |       | start_date, end_date              |
| sport_category (ROAD/TRAIL/HIKE)  |       | status (ACTIVE/COMPLETED)         |
| started_at (TIMESTAMPTZ)          |       +-----------------------------------+
| duration_seconds (INT)            |                          |1
| distance_meters (NUMERIC)         |                          |
| elevation_gain_meters (NUMERIC)   |                          v N
| tss_score (NUMERIC)               |       +-----------------------------------+
| session_rpe (INT)                 |       |            MICROCICLOS            |
| processing_status                 |       +-----------------------------------+
+-----------------------------------+       | id (UUID PK)                      |
                 |1                         | plan_id (UUID FK)                 |
                 v 1                        | week_number (INT)                 |
+-----------------------------------+       | phase (BASE/BUILD/PEAK/TAPER)     |
|     ACTIVITY_TELEMETRY_SUMMARY    |       | target_volume_hours, target_tss   |
+-----------------------------------+       +-----------------------------------+
| id (UUID PK)                      |                          |1
| activity_id (UUID FK)             |                          |
| avg_hr, max_hr (INT)              |                          v N
| avg_vam_vertical_speed_mh         |       +-----------------------------------+
| hr_zones_distribution (JSONB)     |       |         WORKOUT_SESSIONS          |
| raw_series_bucket_key (VARCHAR)   |       +-----------------------------------+
+-----------------------------------+       | id (UUID PK)                      |
                                            | microcycle_id (UUID FK)           |
                                            | day_of_week (1-7), is_rest_day    |
                                            | session_category                  |
                                            | duration_min, exercise_list(JSONB)|
                                            | nutrition_guidelines (JSONB)      |
                                            | recovery_prescriptions (JSONB)    |
                                            +-----------------------------------+
```

#### 7.2 Especificación de Endpoints REST Clave

##### A. Ingesta Asíncrona de Archivos

* **Endpoint:** `POST /api/v1/activities/upload`
* **Headers:** `Authorization: Bearer <token>`, `Content-Type: multipart/form-data`
* **Payload:** `file: [binary payload .fit | .gpx | .csv]`
* **Respuesta Exitosa (HTTP 202 Accepted):**

```json
{
  "job_id": "job_9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "QUEUED",
  "file_name": "entrenamiento_pichincha.fit",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "estimated_processing_time_ms": 1200
}
```

##### B. Logging de Actividad Manual

* **Endpoint:** `POST /api/v1/activities/manual`
* **Headers:** `Authorization: Bearer <token>`, `Content-Type: application/json`
* **Payload:**

```json
{
  "sport_category": "STRENGTH",
  "started_at": "2026-09-17T07:00:00Z",
  "duration_minutes": 50,
  "session_rpe": 8,
  "notes": "Sentadilla goblet, desplantes búlgaros y core"
}
```

* **Respuesta Exitosa (HTTP 201 Created):**

```json
{
  "activity_id": "act_8a2d1f90-1c3e-4b72-9112-7f3e8b1d9c22",
  "source_type": "MANUAL",
  "calculated_load": 400.0,
  "created_at": "2026-09-17T07:55:00Z"
}
```

##### C. Configuración de Meta Parametrizada

* **Endpoint:** `POST /api/v1/profiles/me/goals`
* **Headers:** `Authorization: Bearer <token>`, `Content-Type: application/json`
* **Payload:**

```json
{
  "discipline": "TRAIL_RUNNING",
  "subgoal_type": "TRAIL_MARATHON",
  "custom_distance_km": 42.195,
  "target_elevation_gain_m": 2400,
  "target_date": "2026-12-20",
  "available_days_per_week": 5
}
```

* **Respuesta Exitosa (HTTP 200 OK):**

```json
{
  "goal_id": "c7a884f4-5b29-4d64-8843-982f6e987c12",
  "weeks_to_target": 13,
  "status": "INITIALIZED",
  "redirect_url": "/planner"
}
```

---

### 8. Matriz de Riesgos Principales y Mitigación

| Riesgo Técnico / Operativo | Severidad | Probabilidad | Estrategia de Mitigación Implementada |
| :--- | :--- | :--- | :--- |
| **Variabilidad en esquemas .FIT de fabricantes** | ALTA | ALTA | FIT SDK oficial complementado con sanitización canónica que extrae campos esenciales e ignora etiquetas propietarias. |
| **Sobrecarga por ingesta masiva concurrente** | ALTA | MEDIA | Desacoplamiento total con colas Redis/BullMQ, rate limiting (25 MB máx) y workers elásticos. |
| **Prescripción de cargas lesivas por descontrol** | CRÍTICA | BAJA | Motor 100% determinista basado en reglas científicas (progresión $\le 10\%$ y descanso forzado si ACWR > 1.5). |
| **Fricción por ausencia de wearables en principiantes** | ALTA | ALTA | Onboarding didáctico guiado con método CaCo, screening sin jerga y registro rápido sRPE (Foster). |
| **Confusión de pautas nutricionales con medicina clínica** | MEDIA | MEDIA | Disclaimer legal vinculante tipificando las recomendaciones como sugerencias de rendimiento deportivo. |
| **Falsos positivos de altitud por ruido barométrico** | MEDIA | MEDIA | Filtro de media móvil con umbral de histéresis de 3 metros para descartar oscilaciones espurias de elevación. |

---

### 9. Protocolo de Handoff (Definition of Ready / Done)

#### 9.1 Definition of Ready (DoR) — Requisitos para Iniciar un Ticket

* El ticket cuenta con una Historia de Usuario estructurada en formato INVEST.
* Los criterios de aceptación están redactados en sintaxis formal Gherkin (Given-When-Then).
* Los contratos de entrada y salida (JSON Schemas / Zod DTOs) están definidos en `@shared/contracts`.
* Las pruebas de regresión y fixtures necesarias (.FIT, .GPX, .CSV sintéticos) están disponibles en `/data/fixtures`.

#### 9.2 Definition of Done (DoD) — Requisitos para Cerrar un Ticket

* Código desarrollado en TypeScript estricto sin uso de `any`.
* Cobertura de pruebas unitarias al 100% en componentes matemáticos fisiológicos (`/src/core/math/`).
* Tests de integración que validan escenarios de éxito (Happy Path) y de borde (archivos corruptos, offsets incorrectos, rangos inválidos).
* Linter y formateador ejecutados sin advertencias (`eslint`, `prettier`).
* Documentación técnica y ADRs actualizados en `/docs/architecture/adrs`.
