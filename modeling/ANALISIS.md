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
