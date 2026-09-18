# Páramo Urbano: Visión General del Proyecto

## Propósito
Plataforma SportTech de periodización determinista y telemetría para corredores de asfalto, trail runners y senderistas.

## Reglas Inmutables de Dominio
1. El cálculo de carga es estrictamente algorítmico y determinista (Banister EWMA: CTL ventana 42, ATL ventana 7, TSB = CTL - ATL).
2. Control lesivo: Sweet spot ACWR entre 0.8 y 1.3. Alarma y descanso obligatorio con ACWR > 1.5.
3. Sobrecarga progresiva: Los incrementos semanales de volumen no deben exceder el 10%.
4. Fecha objetivo (target_date): Bloqueo estricto de fechas menores a 14 días a futuro.
