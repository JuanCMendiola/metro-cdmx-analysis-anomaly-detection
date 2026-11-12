# Prepara los datos compactos que usa el dashboard (dashboard/data/*.parquet).
# El dashboard no lee data/processed/ (no se sube a git), asi que puede
# desplegarse en Streamlit Community Cloud solo con lo que hay en el repo.
#
# Correr despues de modeling/prophet_mad.py y modeling/modelado.ipynb, con la
# raiz del repo como working directory:
#   python dashboard/preparar_datos.py

import os
import pandas as pd

SALIDA = 'dashboard/data'
os.makedirs(SALIDA, exist_ok=True)

# Serie diaria por estacion: afluencia real, pronostico de Prophet (historico + futuro) y prioridad
series = pd.read_pickle('data/processed/prophet_series.pkl')
series = series[['ds', 'linea', 'estacion', 'afluencia', 'yhat', 'yhat_lower', 'yhat_upper',
                 'zscore_robusto', 'prioridad_auditoria', 'es_futuro']].rename(columns={'ds': 'fecha'})
series['fecha'] = pd.to_datetime(series['fecha'])
for col in ['afluencia', 'yhat', 'yhat_lower', 'yhat_upper', 'zscore_robusto']:
    series[col] = series[col].astype('float32')
for col in ['linea', 'estacion', 'prioridad_auditoria']:
    series[col] = series[col].astype('category')
series.to_parquet(f'{SALIDA}/series_estaciones.parquet', index=False)

# Propuesta de riesgo futuro (modelo XGBoost + Prophet)
pd.read_csv('propuesta_anomalias_futuras.csv').to_parquet(f'{SALIDA}/riesgo_top_estaciones.parquet', index=False)
alerta = pd.read_excel('propuesta_anomalias_futuras.xlsx', sheet_name='Dias en alerta')
alerta['fecha'] = pd.to_datetime(alerta['fecha'])
alerta.to_parquet(f'{SALIDA}/riesgo_dias_alerta.parquet', index=False)

print(f"Serie diaria: {len(series):,} filas ({series['fecha'].min().date()} -> {series['fecha'].max().date()}) | "
      f"riesgo: {len(alerta):,} dias en alerta")
print('Archivos en', SALIDA, ':', {f: f'{os.path.getsize(os.path.join(SALIDA, f)) / 1e6:.1f} MB' for f in os.listdir(SALIDA)})
