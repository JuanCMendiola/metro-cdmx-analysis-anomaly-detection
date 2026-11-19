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
| `datos/bitacora_validacion_predicciones_final.csv` | OSINT consolidada: 79 estación-días investigados (columnas originales de la plantilla + `Afluencia_Real_SEMOVI`) |
| `datos/bitacora_validacion_registro_de_cambios.csv` | Cada celda que cambió entre la bitácora capturada por el equipo (12-nov-2026) y la consolidada, con el motivo |
| `datos/propuesta_anomalias_futuras_corrida_validacion.xlsx` | Corrida del modelo de la que salió la muestra (950 días en alerta, hojas de muestreo e instrucciones). **No** es la salida actual del notebook: la celda que escribe `propuesta_anomalias_futuras.xlsx` la sobrescribiría, por eso va con otro nombre |
| `datos/afluenciastc_desglosado_2026-01_a_2026-09.csv` | Afluencia diaria desglosada de SEMOVI (datos.cdmx.gob.mx), 1-ene a 30-sep-2026, tal como se descargó |
| `resultados/tasas_osint_por_estrato.csv` | Conteos Sí / Parcial / No por estrato, tasas y tasa ponderada |
| `resultados/causas_osint_prediccion.csv` | Distribución de causas (`Hallazgo_Principal`) |
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

De este criterio dependen las tasas, así que debe declararse tal cual.

- **Sí, evento confirmado.** Una fuente documenta ese día un hecho capaz de alterar la afluencia
  en la estación, su línea o estaciones cercanas (falla en la línea, marcha de seguridad en la
  línea por lluvia, evento masivo junto a la estación).
- **Parcial, evento cercano o indirecto.** El hecho existe pero es de toda la ciudad o su relación
  con la estación es indirecta (feriado, lluvia general, evento a varias estaciones o en las cercanías).
- **No, sin evento.** Se investigó y no se encontró causa: ruido o falsa alarma.
- **Sin información suficiente.** No hay fuentes para decidir.

El Hoy No Circula habitual no cuenta como causa (aplica todos los días); solo una contingencia
ambiental declarada. El 16 de septiembre y el Día de Muertos se clasifican como
`Feriado No Oficial / Cultural`; `Evento Cívico / Jornada Electoral` queda solo para jornadas electorales.

### Ajustes de consolidación (12-nov-2026)

Se conserva la clasificación del equipo con estos cambios (detalle en el registro de cambios
y en `Observaciones`):

- **Captura:** campos vacíos, links incompletos y formato de fecha.
- **Hoy No Circula:** VAL-052, 070, 072, 075, 077 y 079 pasan a "No"; no hubo contingencia y no se encontró otra causa.
- **Feriados:** las filas del 16-sep y 2-nov en "No" o "Sin información" pasan a "Parcial".
- **VAL-016:** el link era de Aquiles Serdán, Chihuahua; se reemplazó por el horario festivo del Metro ("Parcial").
- **VAL-031:** el incendio de la Línea B fue el 4-nov, no el 2; queda "Parcial" por Día de Muertos.
- **Afluencia real:** `Afluencia_Real_SEMOVI` en las 49 filas con dato publicado.

## Cómo leer las tasas

- **Tasa de Sí** = filas "Sí" / filas investigadas del estrato. Proporción de alertas con evento directo.
- **Tasa de Sí + Parcial** = proporción de alertas en que pasó algo, directo o indirecto. Si la
  diferencia con la de Sí es grande (como en Alta), el modelo acertó sobre todo días de calendario
  atípico y no hechos propios de cada estación.
- **Tasa ponderada** = Σ N_h · tasa_h / 417. Estima qué se habría encontrado investigando los 417
  días. No es 34/79 (43%) porque Alta está sobrerrepresentada en la muestra (42 de 79) frente al
  universo (42 de 417). Como Control pesa 74%, la ponderada se parece a la de Control.
- **Tasa de anomalía real** (SEMOVI): proporción de días en alerta cuya afluencia real fue CRÍTICA
  (fuera de la banda 95% de Prophet **y** |z robusto MAD| > 3.5), la misma etiqueta que el modelo
  predice. Se compara contra la tasa histórica de días críticos, cerca de 3% (`modeling/ANALISIS.md`).
  Los cierres no cuentan como anomalía.

## Resultados

### OSINT (79 filas)

| Estrato | Filas | Sí | Parcial | No | Sin info | Tasa Sí | Tasa Sí + Parcial |
|---|---|---|---|---|---|---|---|
| A - Alta | 42 | 10 | 32 | 0 | 0 | 24% | 100% |
| B - Media | 10 | 6 | 2 | 2 | 0 | 60% | 80% |
| C - Control | 27 | 18 | 3 | 5 | 1 | 67% | 78% |
| Ponderado (417) | | | | | | 61% | 80% |

Causas: Feriado No Oficial / Cultural 34%, Evento Masivo 23%, Clima Extremo 18%, Falsa Alarma 10%,
Falla Oculta 6%; el resto 1 a 3% cada una.

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

- El modelo anticipa bien los días de calendario atípico: Alta son dos fechas (16-sep, 30 filas;
  2-nov, 12 filas) y el 16-sep toda la red cayó a cerca del 36% de lo normal.
- En eventos propios de una estación el acierto es menor: 24% de "Sí" directo en Alta.
- Las críticas reales en días en alerta (13%) son unas 4 veces la tasa histórica (~3%); sin el 16-sep, 10%.
- OSINT y afluencia real coinciden en 38 de las 49 filas que tienen ambos; los desacuerdos son
  sobre todo días con lluvia documentada y afluencia normal.

## Gráficas

- `img/01_causas_historico_vs_prediccion.png`: % de cada causa en la OSINT histórica (371 anomalías
  críticas, 2022 a mar-2026) vs la OSINT de las predicciones (79).
- `img/02_calendario_riesgo_historico_vs_prediccion.png`: causa × mes en ambas bitácoras.
- `img/03_osint_por_nivel_de_riesgo.png`: Sí / Parcial / No por estrato.
- `img/04_afluencia_real_por_nivel_de_riesgo.png`: % de días con anomalía CRÍTICA real por estrato frente al ~3% histórico.

## Límites

- **Criterio amplio.** Sí y Parcial aceptan hechos de toda la ciudad; lluvia y feriados ocurren
  muchos días, así que la OSINT sola no prueba que el modelo distinga días de riesgo. Por eso se
  reporta junto con la afluencia real.
- **Sin grupo de comparación.** Las 79 filas son días en alerta; no se investigaron días sin alerta.
- **Muestras chicas.** Media 10 filas, Control 27: margen de error amplio.
- **Datos reales parciales.** SEMOVI llegaba al 30-sep-2026; faltan octubre y noviembre (incluido el 2-nov).
  Al publicarse, basta con reemplazar el CSV de `datos/` y actualizar `SEMOVI` en el script.
- **Fuentes volátiles.** Las notas "en vivo" cambian durante el día; conviene guardar captura de cada fuente.
- **Histórico de otra versión.** La OSINT histórica se hizo sobre una versión anterior del detector,
  así que la comparación de causas (gráficas 01 y 02) es descriptiva.
- **Reproducibilidad del sorteo.** El script que generó la corrida y sorteó la muestra no está en el repo.
