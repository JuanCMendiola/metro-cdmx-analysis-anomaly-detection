# Modelado: Prophet + MAD, riesgo futuro con XGBoost (horizonte 6 meses)

Estado vigente del notebook `modeling/modelado.ipynb` (corrida 2026-10-28,
datos 2022-01-01 a 2026-07-31, 196 series estación-línea, 195 activas).
Presentación visual: `presentacion_prophet_mad_xgboost.pdf` (raíz del repo).

## 1. Detector: Prophet + MAD estacional

| Paso | Qué hace | Dónde |
|---|---|---|
| Cierres operativos | Afluencia 0 o < 5% de la mediana de los 5 días equivalentes previos -> `CIERRE (Operativo)`; no cuenta como anomalía | celda 4: `UMBRAL_CIERRE`, `es_cierre` |
| MAD estacional | Mediana/MAD de las últimas 5 semanas del mismo día (solo días válidos); anomalía si \|z robusto\| > 3.5 | celda 4: `movil_sin_cierres()` |
| Prophet | Tendencia + estacionalidad anual/semanal + festivos MX, banda 95%; entrena sin cierres; `yhat` y banda >= 0 | celda 8 |
| Consenso | MAD y Prophet -> CRÍTICA; solo Prophet -> ALTA; solo MAD -> MEDIA | celda 8: `conditions` |
| Pronóstico | `DIAS_FUTURO = 182` (6 meses: 2026-08-01 -> 2027-01-29) | celda 8 |

Salidas: `master_auditoria_consenso_MAD.csv/.xlsx` (anomalías, sin cierres),
`data/processed/prophet_series.pkl` (histórico + 6 meses con `yhat`, banda y
componentes `holidays`, `yearly`, `trend`) y una gráfica por serie en
`modeling/img_pronosticos/<linea>/<estacion>.png`.

Conteo histórico (326,235 estación-días): CRÍTICA 8,575 (2.6%), ALTA 6,732,
MEDIA 49,742, CIERRE 23,138 (7.1%).

## 2. Riesgo de anomalía futura (XGBoost sobre Prophet)

Para cada estación-día futuro estima la probabilidad de terminar como CRÍTICA.
Entrena con el universo estación-día de `prophet_series.pkl`, sin cierres.

| Grupo | Variables | Fuente |
|---|---|---|
| Prophet | `yhat_rel`, `banda_rel`, `efecto_festivo_rel`, `estacional_anual_rel` | pronóstico de Prophet, normalizado vs el mismo día de la semana de la estación |
| Calendario | mes, semana, día del mes, festivo, días a/desde festivo, cercanía a Semana Santa | `holidays` (MX) + `dateutil.easter` |
| Feriados no oficiales | `es_feriado_no_oficial` (`FECHAS_CULTURALES`) | bitácora OSINT |
| Clima | temporadas de lluvias, calor y contingencia | climatología CDMX (no hay clima diario futuro) |
| Estación | `linea_cod`, tasa histórica de críticas (total y al alza), `log_demanda`, `percentil_demanda`, `cv_demanda` | histórico, solo tramo de entrenamiento |
| Excluidas | `dia_semana`, `es_fin_semana` | se quitan + pesos por día para no aprender "fin de semana = riesgo" |

Las variables más importantes son `es_feriado_no_oficial`, `dias_a_semana_santa`,
`mes` y `temporada_calor`; de Prophet, `efecto_festivo_rel`.

Propuesta (celda 28): `propuesta_anomalias_futuras.csv` (Top 30 estaciones por
riesgo promedio) y `.xlsx` (hojas "Top estaciones" y "Dias en alerta", riesgo >= 2x
frente a un día típico del mismo día de la semana).

## 3. Resultados

### Validación del notebook (corte 2025-08-31, prevalencia 3.3%)

| Modelo | AP global | ROC-AUC global | AP intra-día | ROC-AUC intra-día |
|---|---|---|---|---|
| Solo día de la semana | 0.039 | 0.555 | 0.033 | 0.500 |
| Tasa histórica de la estación | 0.031 | 0.480 | 0.031 | 0.474 |
| XGBoost sin Prophet | 0.313 | 0.717 | 0.257 | 0.709 |
| **XGBoost + Prophet (elegido)** | 0.312 | 0.738 | **0.269** | 0.731 |
| XGBoost + Prophet con día de semana (contraste) | 0.340 | 0.736 | 0.281 | 0.735 |

Esta validación usa `yhat` dentro de muestra, así que no depende del horizonte.

### Backtest fuera de muestra: 3 vs 6 meses

Prophet y XGBoost se reentrenan solo con datos hasta el corte y se evalúan con
el pronóstico de ese corte (sin días de cierre, 195 estaciones).

**Prophet**

| Horizonte | Evalúa | WAPE | MAPE mediana | Cobertura banda 95% |
|---|---|---|---|---|
| 3 meses (corte 30-abr) | may-jul 2026 | 10.4% | 9.3% | 93.8% |
| 6 meses (corte 31-ene) | feb-jul 2026 | 12.5% | 11.9% | 89.4% |
| 6 meses, meses 4-6 | may-jul 2026 | 13.6% | 11.8% | 87.6% |

**XGBoost + Prophet**

| Horizonte | AP intra-día | vs azar | Precision@30 | Recall@30 |
|---|---|---|---|---|
| 3 meses (may-jul) | 0.048 | 1.9x | 3.7% | 23% |
| 6 meses (feb-jul) | 0.303 | 9.8x | 4.1% | 21% |
| 6 meses, meses 1-3 (feb-abr) | 0.417 | 11.3x | 5.1% | 21% |
| 6 meses, meses 4-6 (may-jul) | 0.039 | 1.6x | 3.2% | 20% |

Lectura:

- **A 6 meses las métricas no mejoran.** Comparando los mismos meses (may-jul),
  Prophet pasa de WAPE 10.4% a 13.6% y la cobertura de la banda baja de 93.8% a
  87.6%; XGBoost baja de AP intra-día 0.048 a 0.039.
- El AP alto del tramo feb-abr viene de Semana Santa (2-4 abr 2026, ~470
  críticas), que el calendario sí anticipa.
- May-jul es difícil para cualquier horizonte: el 11-jun-2026 (inauguración del
  Mundial) salieron 153 estaciones en CRÍTICA y ninguna variable lo describe.
- El horizonte de 6 meses sirve para planear (picos esperados: 15-sep, 2-nov,
  24-dic, 1-ene); para operar conviene recalcular cada mes.
- Top de la propuesta: Chabacano L9, Ciudad Deportiva L9, Chabacano L8 (cambio de
  nivel en 2026 que no se separa como cierre), luego estaciones de L1.

## 4. Limitaciones y siguientes pasos

- La etiqueta es lo que detectan Prophet + MAD, no incidentes confirmados; la
  muestra OSINT y la bitácora corresponden a una versión anterior del detector.
- Cierres parciales / cambios de nivel (Chabacano L9, Balderas, Zócalo) inflan el
  riesgo de esas estaciones.
- Falta un calendario de eventos (conciertos, partidos, marchas) y clima diario.
- La banda de Prophet pierde cobertura a 6 meses: probar intervalos conformales
  calibrados por horizonte.

## Dependencias

`prophet`, `xgboost` (opcional; sin él solo Random Forest), `holidays` y
`python-dateutil` en `requirements.txt`.
