# Validación de las predicciones: OSINT y afluencia real

Comprueba si los días que el modelo de riesgo (Prophet + XGBoost, `modeling/modelado.ipynb`)
marcó en alerta tuvieron de verdad algo atípico. Se hace sobre meses que el modelo no vio
(agosto a noviembre de 2026) con dos pruebas independientes:

- **OSINT** (manual): ¿pasó algo ese día en la estación, su línea o la ciudad?
- **Afluencia real de SEMOVI** (código): ¿la afluencia fue atípica según el mismo detector del repo?

La investigación OSINT se hizo a mano; el código solo la lee para calcular tasas y gráficas.

## Archivos

| Archivo | Qué es |
|---|---|
| `validacion_predicciones.py` | Calcula estratos, tasas de la OSINT, cruce con SEMOVI y las 4 gráficas. Se corre desde la raíz del repo |
| `datos/bitacora_validacion_predicciones_original.csv` | **Fuente vigente.** OSINT original del equipo: 79 estación-días investigados, tal como se capturó en la hoja de cálculo (fechas m/d/aaaa, afluencia con comas de miles, `Afluencia_Real_SEMOVI` vacía) |
| `datos/respaldo_version_corregida/` | Versión corregida anterior (`bitacora_validacion_predicciones_final.csv`) y su registro de cambios. **Ya no se usa**: el equipo determinó que esa corrección era incorrecta. Se conserva solo como respaldo |
| `datos/propuesta_anomalias_futuras_corrida_validacion.xlsx` | Corrida del modelo de la que salió la muestra (950 días en alerta, hojas de muestreo e instrucciones). **No** es la salida actual del notebook: la celda que escribe `propuesta_anomalias_futuras.xlsx` la sobrescribiría, por eso va con otro nombre |
| `datos/afluenciastc_desglosado_2026-01_a_2026-09.csv` | Afluencia diaria desglosada de SEMOVI (datos.cdmx.gob.mx), 1-ene a 30-sep-2026, tal como se descargó |
| `resultados/tasas_osint_por_estrato.csv` | Conteos Sí / Parcial / No por estrato, tasas y tasa ponderada |
| `resultados/causas_osint_prediccion.csv` | Distribución de causas (`Hallazgo_Principal`; las 2 filas sin causa capturada salen como "Sin causa registrada") |
| `resultados/osint_vs_afluencia_real.csv` | Las 49 filas de la bitácora con dato de SEMOVI: respuesta OSINT, afluencia real, etiqueta del detector y si coinciden |
| `resultados/dias_en_alerta_vs_afluencia_real.csv` | Los 230 días en alerta con dato real: esperado, banda, real, z robusto y etiqueta del detector |
| `resultados/tasas_afluencia_real_por_estrato.csv` | Tasa de anomalía CRÍTICA real y de cualquier anomalía por estrato |
| `img/01` a `img/04` | Gráficas (ver abajo) |

## Metodología de la OSINT

1. **Punto de partida.** La hoja "Dias en alerta" de la corrida: 950 estación-días entre el
   2-ago-2026 y el 28-ene-2027 con riesgo al menos 2 veces el de un día típico del mismo día de la semana.
2. **Universo.** Solo fechas ya ocurridas al corte del 5-nov-2026: 417 estación-días.
3. **Estratos** por probabilidad de anomalía CRÍTICA (percentiles del universo).
4. **Muestra.** 79 filas (Cochran, 95% de confianza, ±10 pts, corrección por población finita).
   Alta se revisa completa; Media y Control se sortean (semilla 42) repartidos por mes.
5. **Investigación a ciegas.** Mismo esfuerzo por fila sin ver la probabilidad. Fuentes: X de
   @MetroCDMX, noticias, comunicados de SEMOVI y STC, agenda de eventos.
6. **Registro.** Si ocurrió un evento, causa (`Hallazgo_Principal`), descripción y links.

| Estrato | Probabilidad | Universo (N_h) | Investigadas | Selección |
|---|---|---|---|---|
| A - Alta | ≥ P90 (0.1208) | 42 | 42 | Censo |
| B - Media | P75 (0.083) a P90 | 66 | 10 | Sorteo |
| C - Control | < P75 | 309 | 27 | Sorteo |
| Total | | 417 | 79 | |

### Criterio de confirmación

De este criterio dependen las tasas, así que debe declararse tal cual. Son las categorías de la
plantilla, aplicadas por el equipo al investigar:

- **Sí, evento confirmado.** Se encontró un hecho ese día que el equipo relacionó con la estación
  (en la bitácora original incluye lluvias intensas, eventos masivos y fallas).
- **Parcial, evento cercano o indirecto.** El hecho existe pero su relación con la estación es
  indirecta (por ejemplo feriados, Hoy No Circula o un evento en otra zona). Un feriado cuenta
  como Parcial aunque no se haya encontrado nada en la estación.
- **No, sin evento.** Se investigó y no se encontró causa: ruido o falsa alarma.
- **Sin información suficiente.** No hay fuentes para decidir. Es una categoría aparte: no cuenta
  como Sí ni como Parcial, pero sí en el total de filas del estrato.

### Versión de la bitácora que se usa

Se usa la bitácora **original** del equipo, sin las correcciones de la versión consolidada del
12-nov-2026 (reclasificación de Hoy No Circula, cambios en VAL-016 y VAL-031, 2-nov). Esa versión quedó en `datos/respaldo_version_corregida/`
como respaldo.

**Único ajuste (25-nov-2026):** las 15 filas del 16-sep (Independencia, feriado) calificadas "No"
pasan a "Parcial", porque aunque no se encontró nada en la estación el día es feriado. Se aplica en
el script (`FERIADO_AJUSTE`), no en el CSV, que se conserva tal como se capturó. Solo cambia la
calificación: la causa (`Hallazgo_Principal`) queda como la registró el equipo, así que esas filas
siguen contando como "Falsa Alarma" (13) o sin causa (2) en las gráficas de causas. La fila del
16-sep con "Sin información suficiente" no cambia.

La columna `Afluencia_Real_SEMOVI` de la original viene vacía; el cruce con la afluencia real lo
hace el script directamente con el CSV de SEMOVI.

## Cómo leer las tasas

- **Tasa de Sí** = filas "Sí" / filas investigadas del estrato. Proporción de alertas con evento directo.
- **Tasa de Sí + Parcial** = proporción de alertas en que pasó algo, directo o indirecto. Si la
  diferencia con la de Sí es grande (como en Alta), el modelo acertó sobre todo días de calendario
  atípico y no hechos propios de cada estación.
- **Tasa ponderada** = Σ N_h · tasa_h / 417. Estima qué se habría encontrado investigando los 417
  días. No es 37/79 (47%) porque Alta está sobrerrepresentada en la muestra (42 de 79) frente al
  universo (42 de 417). Como Control pesa 74%, la ponderada se parece a la de Control.
- **Tasa de anomalía real** (SEMOVI): proporción de días en alerta cuya afluencia real fue CRÍTICA
  (fuera de la banda 95% de Prophet **y** |z robusto MAD| > 3.5), la misma etiqueta que el modelo
  predice. Se compara contra la tasa histórica de días críticos, cerca de 3% (`modeling/ANALISIS.md`).
  Los cierres no cuentan como anomalía.

## Resultados

### OSINT (79 filas)

| Estrato | Filas | Sí | Parcial | No | Sin info | Tasa Sí | Tasa Sí + Parcial |
|---|---|---|---|---|---|---|---|
| A - Alta | 42 | 11 | 28 | 2 | 1 | 26% | 93% |
| B - Media | 10 | 7 | 2 | 1 | 0 | 70% | 90% |
| C - Control | 27 | 19 | 7 | 0 | 1 | 70% | 96% |
| Total muestra | 79 | 37 | 37 | 3 | 2 | 47% | 94% |
| Ponderado (417) | | | | | | 66% | 95% |

Causas: Evento Masivo 24%, Falsa Alarma 23%, Clima Extremo 16%, Feriado No Oficial / Cultural 9%,
Contingencia Ambiental 9%, Falla Oculta 8%; el resto 1 a 4% cada una (2 filas sin causa capturada).

### Afluencia real de SEMOVI (230 días en alerta, 2-ago a 30-sep-2026)

| Estrato | Días | Anomalía CRÍTICA real | Alguna anomalía real |
|---|---|---|---|
| A - Alta | 30 | 11 (37%) | 28 (93%) |
| B - Media | 33 | 2 (6%) | 9 (27%) |
| C - Control | 167 | 18 (11%) | 86 (51%) |
| Total | 230 | 31 (13%) | 123 (53%) |
| Total sin el 16-sep | 200 | 20 (10%) | 95 (48%) |

En los días en alerta la afluencia real quedó en mediana 20% por debajo de lo que pronosticó
Prophet y solo 61% cayó dentro de su banda.

### Lectura conjunta

- **El modelo anticipa bien los días de calendario atípico.** Alta son dos fechas (16-sep, 30 filas;
  2-nov, 12 filas) y en 93% de sus filas pasó algo (Sí o Parcial). El 16-sep toda la red cayó a cerca
  del 36% de lo normal: 28 de los 30 días de Alta con dato real tuvieron alguna anomalía y 11 fueron
  CRÍTICA (37%).
- **En eventos propios de una estación el acierto es menor:** Alta tiene la tasa de Sí más baja (26%);
  la mayoría de sus filas son Parcial por el feriado. Medio y Control tienen 70% de Sí, así que la OSINT
  no separa los niveles de riesgo en el orden esperado.
- **OSINT y afluencia real coinciden en 36 de las 49 filas con ambos datos** (OSINT Sí o Parcial
  frente a cualquier anomalía real). El desacuerdo principal es fuera del 16-sep: 9 de 16 filas "Sí"
  tuvieron afluencia normal, sobre todo días con lluvia documentada.
- Las críticas reales en días en alerta (13%) son unas 4 veces la tasa histórica (~3%); sin el 16-sep, 10%.

## Gráficas

- `img/01_causas_historico_vs_prediccion.png`: % de cada causa en la OSINT histórica (371 anomalías
  críticas, 2022 a mar-2026) vs la OSINT de las predicciones (79).
- `img/02_calendario_riesgo_historico_vs_prediccion.png`: causa × mes en ambas bitácoras.
- `img/03_osint_por_nivel_de_riesgo.png`: Sí / Parcial / No / Sin información por estrato.
- `img/04_afluencia_real_por_nivel_de_riesgo.png`: % de días con anomalía CRÍTICA real por estrato frente al ~3% histórico.

## Límites

- **Criterio amplio.** Sí y Parcial aceptan hechos de toda la ciudad (la lluvia intensa se registró
  como "Sí"); lluvia, feriados y Hoy No Circula ocurren muchos días, así que la OSINT sola no prueba
  que el modelo distinga días de riesgo. Por eso se reporta junto con la afluencia real.
- **Contingencia Ambiental.** Las 7 filas con esta causa (19, 26 y 27-oct, 3-nov) describen el
  "Hoy No Circula"; si no hubo contingencia declarada, es el programa habitual que aplica todos los días.
- **Sin grupo de comparación.** Las 79 filas son días en alerta; no se investigaron días sin alerta.
- **Muestras chicas.** Media 10 filas, Control 27: margen de error amplio.
- **Datos reales parciales.** SEMOVI llegaba al 30-sep-2026; faltan octubre y noviembre (incluido el 2-nov).
  Al publicarse, basta con reemplazar el CSV de `datos/` y actualizar `SEMOVI` en el script.
- **Fuentes volátiles.** Las notas "en vivo" cambian durante el día; conviene guardar captura de cada fuente.
- **Histórico de otra versión.** La OSINT histórica se hizo sobre una versión anterior del detector,
  así que la comparación de causas (gráficas 01 y 02) es descriptiva.
- **Reproducibilidad del sorteo.** El script que generó la corrida y sorteó la muestra no está en el repo.
