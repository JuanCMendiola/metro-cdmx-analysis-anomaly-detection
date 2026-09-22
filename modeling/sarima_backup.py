# Respaldo del modelado SARIMA/SARIMAX (exploracion de una sola estacion y
# comparativa SARIMA vs Prophet con division train/test) que se removio de
# modeling/modelado.py para quedarnos solo con Prophet. Se conserva aqui tal
# cual para no perder el trabajo, pero ya no forma parte del pipeline activo.
# Contexto y hallazgos: ver modeling/ANALISIS.md.
# Igual que eda/ y feature_engineering/: backend 'Agg' (plt.show() no bloquea
# ni abre ventanas) y cada grafica se guarda en modeling/img_sarima_backup/.
# Autocontenido: carga af_modelo desde el checkpoint que genera
# feature_engineering/feature_engineering.py.

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX
from pmdarima import auto_arima
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error

os.makedirs('modeling/img_sarima_backup', exist_ok=True)

af_modelo = pd.read_pickle('data/processed/af_modelo.pkl')

# %%
af_modelo.isna().sum()

# %%
datos = af_modelo[
    (af_modelo['linea']=='linea 1') &
    (af_modelo['estacion']=='balbuena')
]

serie = datos['afluencia'].dropna().sort_index()

# %%
print(len(serie))

# %%
plt.figure(figsize=(14,5))
plt.plot(serie)
plt.title('Serie de afluencia')
plt.savefig('modeling/img_sarima_backup/01_serie_balbuena.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

# %%
plot_acf(serie, lags=30)
plt.savefig('modeling/img_sarima_backup/02_acf_balbuena.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

# %%
plot_pacf(serie, lags=30)
plt.savefig('modeling/img_sarima_backup/03_pacf_balbuena.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

# %%
resultado = adfuller(serie)

print("p-value:", resultado[1])

# %%
modelo = SARIMAX(
    serie,
    order=(1,1,1),
    seasonal_order=(0,1,1,7)
)

resultado = modelo.fit()

print(resultado.summary())

# %%
resultado.plot_diagnostics(figsize=(12,8))
plt.savefig('modeling/img_sarima_backup/04_diagnosticos_sarimax_balbuena.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

# %%
modelo_auto = auto_arima(
    serie,
    seasonal=True,
    m=7,                 # estacionalidad semanal
    trace=True,          # muestra las pruebas
    stepwise=True,
    suppress_warnings=True
)

print(modelo_auto.summary())

# %%
print(modelo_auto.order)
print(modelo_auto.seasonal_order)

# %%
pred = modelo_auto.predict_in_sample()

plt.figure(figsize=(14,5))
plt.plot(serie, label="Real")
plt.plot(pred, label="Modelo")
plt.legend()
plt.savefig('modeling/img_sarima_backup/05_real_vs_autoarima_balbuena.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

# %%
mae = mean_absolute_error(serie, pred)
print(mae)

# %%
rmse = np.sqrt(mean_squared_error(serie, pred))
print(rmse)

# %%
residuos = serie - pred
residuos

# %%
resultados = {}

for i, (estacion, grupo) in enumerate(af_modelo.groupby("estacion")):

    if i == 2:
        break

    print("Entrenando:", estacion)

    serie_loop = grupo["afluencia"].dropna()

    modelo_loop = auto_arima(
        serie_loop,
        seasonal=True,
        m=7,
        stepwise=True,
        suppress_warnings=True,
        error_action="ignore",
        max_p=2,
        max_q=2,
        max_P=1,
        max_Q=1,
        max_d=1,
        max_D=1
    )

    resultados[estacion] = modelo_loop.order, modelo_loop.seasonal_order

# %%
af_modelo.isna().sum()
datos = af_modelo[
    (af_modelo['linea']=='linea 2') &
    (af_modelo['estacion']=='cuatro caminos')
]

serie = datos['afluencia'].dropna().sort_index()

# %%
print(len(serie))

# %%
plt.figure(figsize=(14,5))
plt.plot(serie)
plt.title('Serie de afluencia - cuatro caminos')
plt.savefig('modeling/img_sarima_backup/06_serie_cuatro_caminos.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

# %%
plot_acf(serie, lags=30)
plot_pacf(serie, lags=30)
plt.savefig('modeling/img_sarima_backup/07_acf_pacf_cuatro_caminos.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

# %%
n_obs = len(serie)
p_max = int(12*(n_obs/100)**0.25) # regla de Schwert
print(f"Numero maximo de rezagos (regla de Schwert): {p_max}")

adf_ct = adfuller(serie, maxlag=p_max, autolag='aic', regression='ct')

for label, res in [("Con constante y tendencia",adf_ct)]:
    print(f"\n--- ADF {label} ---")
    print(f"  Estadistico ADF    : {res[0]:.4f}")
    print(f"  p-valor            : {res[1]:.4f}")
    print(f"  Rezagos usados     : {res[2]}")
    print(f"  Valores criticos   : " +
          "  ".join([f"{k}: {v:.3f}" for k, v in res[4].items()]))
    concl = "Se rechaza H0: serie estacionaria" if res[1] < 0.05 else "No se rechaza H0: posible raiz unitaria"
    print(f"  Conclusion (5%)    : {concl}")

# Grafico: estadistico vs valores criticos
fig, ax = plt.subplots(figsize=(8, 4))
criticos = adf_ct[4]
niveles  = list(criticos.keys())
valores  = list(criticos.values())
colores  = ['#2ecc71' if adf_ct[0] < v else '#e74c3c' for v in valores]
ax.barh(niveles, valores, color=colores, alpha=0.7)
ax.axvline(adf_ct[0], color='black', linewidth=2, linestyle='--',
           label=f'Estadistico ADF (Mod. ct)= {adf_ct[0]:.3f}')
ax.set_xlabel('Valor del estadistico')
ax.set_title('Prueba ADF (con constante y tendencia): estadistico vs. valores criticos')
ax.legend()
plt.tight_layout()
plt.savefig('modeling/img_sarima_backup/08_adf_ct_cuatro_caminos.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

# %%
# 1. Primera diferencia
serie_diff = serie.diff().dropna()
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# Serie original
axes[0].plot(serie)
axes[0].set_title('Serie Original')
axes[0].set_xlabel('Tiempo')
axes[0].set_ylabel('Valor')

# Serie diferenciada
axes[1].plot(serie_diff)
axes[1].set_title('Primera Diferencia')
axes[1].set_xlabel('Tiempo')
axes[1].set_ylabel('Diferencia')

plt.tight_layout()
plt.savefig('modeling/img_sarima_backup/09_primera_diferencia_cuatro_caminos.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

# %%
n_obs = len(serie_diff)
p_max = int(12 * (n_obs / 100) ** 0.25)

print(f"Numero maximo de rezagos (Schwert): {p_max}")

adf_diff = adfuller(
    serie_diff,
    maxlag=p_max,
    autolag='AIC',
    regression='n'
)

print("\n--- ADF: Primera Diferencia ---")
print(f"Estadistico ADF  : {adf_diff[0]:.4f}")
print(f"p-valor          : {adf_diff[1]:.4f}")
print(f"Rezagos usados   : {adf_diff[2]}")
print(
    "Valores criticos : " +
    " | ".join(
        [f"{k}: {v:.4f}" for k, v in adf_diff[4].items()]
    )
)

if adf_diff[1] < 0.05:
    print("Conclusion       : La serie es estacionaria.")
else:
    print("Conclusion       : La serie aun no es estacionaria.")

fig, ax = plt.subplots(figsize=(8, 4))

criticos = adf_diff[4]
niveles = list(criticos.keys())
valores = list(criticos.values())

colores = [
    '#2ecc71' if adf_diff[0] < v else '#e74c3c'
    for v in valores
]

ax.barh(niveles, valores, color=colores, alpha=0.8)
ax.axvline(
    adf_diff[0],
    color='black',
    linestyle='--',
    linewidth=2,
    label=f'ADF = {adf_diff[0]:.3f}'
)

ax.set_xlabel('Valor critico')
ax.set_title('ADF sobre la Primera Diferencia')
ax.legend()

plt.tight_layout()
plt.savefig('modeling/img_sarima_backup/10_adf_primera_diferencia_cuatro_caminos.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

# %%
fig, axes = plt.subplots(2, 1, figsize=(12, 10))

plot_acf(
    serie_diff,
    lags=40,
    ax=axes[0]
)
axes[0].set_title('Funcion de Autocorrelacion (ACF)')

plot_pacf(
    serie_diff,
    lags=40,
    ax=axes[1],
    method='ywm'
)
axes[1].set_title('Funcion de Autocorrelacion Parcial (PACF)')

plt.tight_layout()
plt.savefig('modeling/img_sarima_backup/11_acf_pacf_diferenciada_cuatro_caminos.png', dpi=150, bbox_inches='tight')
plt.show()
plt.close()

# %%
# En los primeros rezagos:
# La ACF muestra un pico negativo en lag 1. La PACF tambien presenta un pico
# significativo en lag 1. Esto sugiere modelos pequenos: AR(1), MA(1), ARMA(1,1).
# Componente estacional: los picos en multiplos de 7 son muy notorios (MA
# estacional en la ACF, cierta persistencia estacional en la PACF).
# Punto de partida recomendado: SARIMA(1,1,1)x(1,0,1)_7 (funciona bien con
# patrones semanales).

# %%
# ============================================
# AutoARIMA para seleccion automatica
# ============================================
modelo_auto = auto_arima(
    serie,
    start_p=0,
    start_q=0,
    max_p=3,
    max_q=3,
    d=1,                  # Ya determinado con ADF
    seasonal=True,
    m=7,                  # Estacionalidad semanal
    start_P=0,
    start_Q=0,
    max_P=2,
    max_Q=2,
    D=None,               # Determinar automaticamente
    trace=True,
    error_action='ignore',
    suppress_warnings=True,
    stepwise=True,
    information_criterion='aic'
)

print(modelo_auto.summary())
print(f"\nMejor modelo encontrado: {modelo_auto.order} x {modelo_auto.seasonal_order}")
print(f"AIC: {modelo_auto.aic():.2f}")
print(f"BIC: {modelo_auto.bic():.2f}")

# %%
# Division 80-20 (misma que usa modeling/modelado.py para Prophet, asi que
# los resultados de ambos modelos son comparables periodo a periodo)
train_size = int(len(serie) * 0.85)

train = serie[:train_size]
test = serie[train_size:]

print(f"Train: {len(train)}")
print(f"Test: {len(test)}")

# %%
# Nota original (celda markdown suelta en el notebook, sin contexto claro):
#   train_log,
#   order=(1,1,1),
#   seasonal_order=(1,0,1,7),   # <- D=1 para estacionalidad semanal
#   enforce_stationarity=False,
#   enforce_invertibility=False

# %%
modelo_sarimax = SARIMAX(
    train,
    order=(1,1,0),
    seasonal_order=(1,0,1,7),
    enforce_stationarity=False,
    enforce_invertibility=False
)

resultado_sarimax = modelo_sarimax.fit(disp=False)

pred_sarimax = resultado_sarimax.forecast(steps=len(test))

# %%
# Pronostico para el horizonte del conjunto de prueba
forecast = resultado_sarimax.get_forecast(steps=len(test))

predicciones = forecast.predicted_mean
intervalos = forecast.conf_int()

# %%
mae = mean_absolute_error(test, predicciones)
rmse = np.sqrt(mean_squared_error(test, predicciones))
mape = mean_absolute_percentage_error(test, predicciones) * 100

print(f"MAE : {mae:,.2f}")
print(f"RMSE: {rmse:,.2f}")
print(f"MAPE: {mape:.2f}%")
