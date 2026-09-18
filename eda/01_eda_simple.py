# EDA sobre el dataset simple 2010-2026 (afluencia diaria agregada).
# Extraido automaticamente de tt.ipynb, celdas [28-33] (sin modificar codigo).

# %% [markdown]
# # **EDA-METRO-SIMPLE-2010-2026**

# %% [markdown]
# - estadística descriptiva
# - herramientas gráficas
# - creatividad
# El análisis exploratorio siempre debe ir acompañado de una pregunta que queramos responder y todo lo que se haga en el análisis debe ser orientado a responder esa pregunta.

# %%
af_dia = metro.groupby('fecha')['afluencia'].sum()
af_dia.to_frame()
af_dia = af_dia.reset_index()
af_dia

# %% [markdown]
# En esta primer serie de tiempo, explica la afluencia diaria del metro de manera general en todas las estaciones, sin tener el nivel de detalle de la linea o estación, es un primer vistazo a la serie de tiempo general diaria de todo el metro de la CDMX.

# %%
# Agrupar por fecha para ver la demanda total del sistema
ts_data = metro.groupby('fecha')['afluencia'].sum().reset_index()

plt.figure(figsize=(15, 6))
plt.plot(ts_data['fecha'], ts_data['afluencia'], label='Afluencia Diaria')
# Media móvil de 7 días para suavizar la serie
ts_data['rolling_7d'] = ts_data['afluencia'].rolling(window=7).mean()
plt.plot(ts_data['fecha'], ts_data['rolling_7d'], color='red', label='Media Móvil (7 días)')

plt.title('Evolución de la Afluencia del Metro en el Tiempo')
plt.xlabel('Fecha')
plt.ylabel('Pasajeros')
plt.legend()
plt.show()

print(round(af_dia['afluencia'].describe(),2))

# %% [markdown]
# *A simple vista se observan patrones de tendencia creciente y ciertos patrones de estacionalidad anual pero sobre todo se nota una diferencia notoria en los datos divididos por la temporada de pandemia, se decidio trabajar con los datos postpandemia a partir de aqui, ya que representan 4 años de datos y aumentando hasta la actualidad (enero 2025)*
