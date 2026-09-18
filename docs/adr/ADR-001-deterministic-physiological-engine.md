# ADR-001: Motor Matemático y Fisiológico Determinista

## Estado
Aprobado (Accepted) — 2026-09-18

## Contexto
Páramo Urbano (v2.0.0 Core) requiere modelar fatiga biológica, estado de forma, ratios de lesión biomecánica y prescripciones de ritmo para corredores de asfalto, trail y senderismo en altitud.
El uso de modelos de lenguaje o aproximaciones heurísticas estocásticas en la cuantificación de cargas o prevención de lesiones deportivas introduce alucinaciones, falta de reproducibilidad y riesgos éticos y de salud física para el atleta.

## Decisión
Implementar un motor fisiológico 100% determinista, auditado y desacoplado de infraestructura (Clean Architecture / Dominio Puro):
1. **Banister Impulse-Response EWMA:** $\tau_1 = 42.0$ días (CTL / Fitness), $\tau_2 = 7.0$ días (ATL / Fatiga), $TSB = CTL - ATL$. Alarma de fatiga crítica cuando $TSB < -25.0$.
2. **ACWR de Tim Gabbett:**
   - Sweet Spot ($0.8 \le ACWR \le 1.3$): Estímulo óptimo.
   - Zona de Precaución ($1.3 < ACWR \le 1.5$): Congelamiento de incrementos de volumen semanal.
   - Zona Crítica ($ACWR > 1.5$): Inyección obligatoria de días de descanso (`requires_mandatory_rest = True`).
3. **Cuantificación Determinista:**
   - Foster sRPE: Carga = Duración (min) * RPE (1-10).
   - rTSS (Running TSS en asfalto plano): Basado en ritmo funcional umbral (FTP pace).
   - hrTSS: Basado en frecuencia cardíaca en umbral de lactato (LTHR).
4. **Filtro de Histéresis Barométrica (3.0 m):**
   - Supresión de microoscilaciones espurias de hardware antes de acumular metros de ascenso (+D) en Trail Running.
5. **Prescripción VDOT (Daniels & Gilbert):**
   - Ecuaciones de costo de oxígeno y drop-dead curve para estimación de VDOT y zonas de entrenamiento (Easy, Marathon, Threshold, Interval, Repetition) con tolerancia GPS simétrica de $\pm 4\text{ seg/km}$.

## Consecuencias
- **Positivas:** Reproducibilidad matemática total, auditoría clínica estricta, cobertura de pruebas unitarias al 100%, compatibilidad con telemetría offline.
- **Negativas:** Requiere validación de umbrales individuales y perfiles basales precisos para maximizar la eficacia de las alertas.
