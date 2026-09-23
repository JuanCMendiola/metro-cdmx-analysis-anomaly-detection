# Analisis y hallazgos - Respaldo de SARIMA

Notas que acompanaban al modelado SARIMA/SARIMAX antes de que ese codigo se
moviera de `modeling/modelado.ipynb` a `modeling/sarima_backup.py` (para
quedarnos solo con Prophet en el notebook activo). El notebook sigue teniendo
sus propias celdas markdown para la parte de Prophet.

- Se puede aplicar una diferenciación estacional, además de incluir modelos
  estacionales AR(P) o MA(Q).
- La prueba Dickey-Fuller aumentada (estación cuatro caminos, con constante y
  tendencia) arrojó un estadístico de -2.6045 y un p-valor de 0.2778. Dado
  que el p-valor es superior a 0.05 y el estadístico no supera el valor
  crítico al 5% (-3.415), no se rechaza la hipótesis nula de raíz unitaria.
  En consecuencia, se concluye que la serie no es estacionaria en niveles.
- Se determina que el orden de diferenciación no estacional es d=1. Este es
  uno de los parámetros clave del modelo SARIMAX: p (orden autorregresivo),
  d (diferenciación), q (media móvil); y si hay estacionalidad: P, D, Q, s.
- En los primeros rezagos: la ACF muestra un pico negativo en lag 1, la PACF
  también presenta un pico significativo en lag 1. Esto sugiere probar
  modelos pequeños como AR(1), MA(1), ARMA(1,1). Componente estacional: los
  picos en múltiplos de 7 son muy notorios (la ACF sugiere un componente MA
  estacional, la PACF muestra también cierta persistencia estacional). Punto
  de partida recomendado: SARIMA(1,1,1)x(1,0,1)_7 (funciona bien con
  patrones semanales).
- Celda suelta sin contexto claro en el notebook original (posiblemente un
  fragmento de parámetros pegado por accidente en una celda markdown):
  ```
  train_log,
  order=(1,1,1),
  seasonal_order=(1,0,1,7),   # <- D=1 para estacionalidad semanal
  enforce_stationarity=False,
  enforce_invertibility=False
  ```

---

# Cambios en modelado.ipynb: gráficas de pronóstico y riesgo de anomalías futuras

Resumen de lo que se agregó al notebook activo y por qué, con las cifras de la
corrida de referencia (195 series, datos 2022-01-01 a 2026-07-31).

## 1. Motor de auditoría (celda "MODELO PARA LAS 195 SERIES")

- **Detección sin cambios:** mismas reglas (Prophet fuera de su intervalo + MAD
  robusto a 7 días -> CRÍTICA / ALTA / MEDIA). `master_auditoria_consenso_MAD.csv`
  conserva sus columnas; solo cambia ligeramente entre corridas porque el
  intervalo de Prophet se estima por muestreo aleatorio (10,937 vs ~10,980
  críticas).
- **Gráfica de pronóstico por serie:** se guarda un PNG por estación en
  `modeling/img_pronosticos/<linea>/<estacion>.png` con (arriba) todo el
  histórico: afluencia real, ajuste de Prophet, intervalo y anomalías por
  prioridad; y (abajo) un zoom a los últimos 90 días + el pronóstico de los
  próximos 30 días. Se controla con `carpeta_graficas` y `dias_futuro`.
- **Pronósticos guardados:** el motor ahora devuelve también `series_prophet`
  (todos los días de cada serie más los días futuros) y lo guarda en
  `data/processed/prophet_series.pkl`, con `yhat`, su intervalo y los
  componentes de Prophet `holidays` (efecto de festivos MX), `yearly` y
  `trend`. Es el insumo del modelo de riesgo.
- **Excel:** `master_auditoria_consenso_MAD.xlsx` es una copia del CSV para
  revisión manual (OSINT); ninguna celda lo lee.

## 2. Riesgo de anomalías futuras (Random Forest / XGBoost sobre Prophet)

Prophet sigue siendo el modelo base. El clasificador **continúa** su
pronóstico: para cada estación-día futuro estima la probabilidad de que el día
termine como anomalía CRÍTICA. El CSV de anomalías solo contiene positivos, por
eso se entrena con el universo completo estación-día de `series_prophet`
(positivo = CRÍTICA, ~3.4% de los días).

Salida: `propuesta_anomalias_futuras.csv` (pronóstico de Prophet con su banda
+ `prob_critica`, `riesgo_relativo`, `riesgo_vs_mismo_dia`, `ranking_en_el_dia`).

### Variables (todas conocibles para fechas futuras)

| Grupo | Variables |
|---|---|
| Extraídas de Prophet | `yhat_rel`, `banda_rel`, `efecto_festivo_rel` (componente `holidays`), `estacional_anual_rel` (componente `yearly`) |
| Calendario / estacionalidad | mes, semana, día del mes, festivos oficiales MX, días a/desde festivo, cercanía a Semana Santa, feriados no oficiales/culturales (`FECHAS_CULTURALES`, salen de la bitácora OSINT) |
| Clima (climatología) | `temporada_lluvias` (jun-oct), `temporada_calor` (mar-may), `temporada_contingencia` (feb-jun) |
| Carácter de la estación | `log_demanda`, `percentil_demanda`, `cv_demanda`, `tasa_hist_estacion`, `tasa_hist_alza` (críticas por picos al alza), `linea_cod` |

El clima diario real no se puede conocer a futuro y no hay datos de clima en el
proyecto, por lo que se usa solo la temporada. Las estadísticas de estación se
calculan únicamente con el tramo de entrenamiento. Jornadas electorales y
manifestaciones concretas no están modeladas (no hay calendario futuro
confiable).

### Cómo se controló el sesgo de fin de semana

Problema: las críticas se concentran en fines de semana (domingo 7.3% de los
estación-días vs 1.9-2.9% entre semana; 31% de todas las críticas son en
domingo). La bitácora OSINT indica que parte de eso es ruido del detector: 45%
de las 75 "Falsas Alarmas" caen en domingo. Un modelo ingenuo aprende "domingo
= riesgo" (predice 3.5x más riesgo en domingo que entre semana) en vez de los
factores que la investigación sí encontró (clima extremo, eventos masivos,
feriados no oficiales, estacionalidad). Medidas:

1. `dia_semana` y `es_fin_semana` **no** son variables del modelo (solo del modelo de contraste).
2. Las variables de Prophet se normalizan contra el **mismo día de la semana de
   cada estación** y no se usa el componente semanal de Prophet.
3. El entrenamiento **pondera por día de la semana**: cada positivo pesa
   `tasa_global / tasa_de_su_día`, igualando la prevalencia entre días.
4. La evaluación se hace **dentro de cada día de la semana** (AP y ROC-AUC
   intra-día), además de la global.
5. La propuesta se ordena por `riesgo_vs_mismo_dia` (riesgo del estación-día
   frente a uno típico del mismo día de la semana).

### Resultados (validación temporal: entrena hasta 2025-08-30, prueba después)

| Modelo | AP global | AP intra-día | ROC-AUC intra-día |
|---|---|---|---|
| Al azar (prevalencia) | 0.039 | 0.039 | 0.500 |
| Referencia: solo día de la semana | 0.055 | 0.039 | 0.500 |
| Referencia: tasa histórica de la estación | 0.042 | 0.043 | 0.510 |
| Random Forest sin variables de Prophet | 0.110 | 0.139 | 0.678 |
| XGBoost sin variables de Prophet | 0.120 | 0.161 | 0.693 |
| Random Forest + Prophet | 0.120 | 0.137 | 0.700 |
| **XGBoost + Prophet (elegido)** | 0.136 | **0.171** | 0.716 |
| XGBoost + Prophet CON día de semana (sesgado, contraste) | 0.152 | 0.186 | 0.727 |

Lectura honesta:

- Hay señal real dentro de cada día (AP intra-día ~4.4x el azar), pero es
  **modesta**: sirve para **priorizar** estaciones/días de vigilancia, no como
  predictor exacto de fallas.
- Las variables de Prophet aportan poco pero de forma consistente con XGBoost
  (AP intra-día 0.161 -> 0.171, ROC-AUC 0.693 -> 0.716); con Random Forest no
  mejoran el AP.
- El sesgo de fin de semana **se redujo, no desapareció**: relación
  domingo/entre semana de 3.5x (sesgado) -> 1.5x (elegido); el detector real
  tuvo 2.3x en el periodo de prueba. Lo que queda es en parte legítimo (fines de
  semana con festivos/puentes) y en parte estaciones con patrón dominical propio
  (p. ej. Copilco, Polanco, Villa de Aragón), por lo que el top de la propuesta
  sigue teniendo muchos domingos.
- Estaciones de mayor demanda tienen una tasa histórica de críticas algo mayor
  (2.9% en el cuartil de menor demanda vs 3.7% en el de mayor), pero la
  variable pesa poco frente al calendario.
- La etiqueta es lo que detectan Prophet + MAD, no incidentes confirmados; en
  el histórico `yhat` es ajuste dentro de muestra.

### Dependencias

`xgboost` (opcional; sin él solo se entrena Random Forest), `holidays` y
`python-dateutil` (ya vienen con Prophet) en `requirements.txt`.
