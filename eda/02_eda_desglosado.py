# EDA sobre el dataset desglosado por linea, estacion y tipo de pago.
# Extraido automaticamente de tt.ipynb, celdas [37-70] (sin modificar codigo).

# %% [markdown]
# # **EDA-METRO-NUEVO-DATASET-DESGLOSADO**

# %% [markdown]
# - estadística descriptiva
# - herramientas gráficas
# - creatividad
# El análisis exploratorio siempre debe ir acompañado de una pregunta que queramos responder y todo lo que se haga en el análisis debe ser orientado a responder esa pregunta.

# %% [markdown]
# En esta agrupacción igual se muestra un análisis general pero tomando en cuenta post-pandemia, que será graficado más adelante, porque como se mencionó los patrones de afluencia cambiaron después de la pandemia

# %%
af_dia = metro.groupby('fecha')['afluencia'].sum()
af_dia.to_frame()
af_dia = af_dia.reset_index()
af_dia

# %%
af_dia_est = metro.groupby(['fecha', 'linea', 'estacion'])['afluencia'].sum()
af_dia_est.to_frame()
af_dia_est = af_dia_est.reset_index()
af_dia_est

# %% [markdown]
# Dataset que servirá más adelante para un análisis más particular donde se tome en cuenta las estaciones y a que línea pertenece

# %%
#el dataset ya no es muy grande, por lo que ahora si se puede guardar como excel
#metro.to_excel('metro_limpio.xlsx', index= False)

# %% [markdown]
# Se observa la serie de tiempo que se ha cortado post-pandemia donde se observa el comportamiento esperado de recuperación de los niveles de afluencia conforme pasa cada año.

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

# %%
df_sin_index = metro.reset_index()
df_sin_index['año'] = df_sin_index['fecha'].dt.year

# %%
af_linea = df_sin_index.groupby(['año','linea','estacion','tipo_pago'])['afluencia'].sum()
af_linea.to_frame()
af_linea = af_linea.reset_index()
af_linea

# %% [markdown]
# Sin tomar en cuenta el año 2026, En el siguiente gráfico se nota con mayor precisión el aumento de la afluencia por año, creciendo aproximadamente 1% cada año, entonces se espera cierta tendencia en las series de tiempo

# %%
#pie chart de la afluencia total por año a partir del 2022 al 2026
af_anual = df_sin_index.groupby('año')['afluencia'].sum().reset_index()
af_anual = af_anual[af_anual['año'] < 2026]
plt.figure(figsize=(8, 8))
plt.pie(af_anual['afluencia'], labels=af_anual['año'], autopct='%1.1f%%', startangle=140)
plt.title('Distribución de Afluencia Total por Año (2022-2025)', fontweight='bold')
plt.show()

# %% [markdown]
# Analizamos la afluencia sumada del periodo de años analizados (2022-2026) pero por línea del metro, para conocer las líneas mas afluenciadas en el periodo completo analizado
#
# El gráfico muestra el siguiente top de lineas mas afluenciadas
# 1. Línea 2 (17.5%)
# 2. Línea 3 (14.9%)
# 3. Línea b (10.9%)
# 4. Línea 8 (10.6%)
# 5. Línea 1 (8.2%)
#

# %%
import matplotlib.pyplot as plt

# Agrupar por línea (por si hay más de un registro por línea)
pie_data = af_linea.groupby('linea')['afluencia'].sum()

# Colores oficiales del Metro CDMX en Hex
colores_linea = {
    'linea 1': '#ED2D8C',   # Rosa mexicano
    'linea 2': '#005DAA',   # Azul
    'linea 3': '#7A8727',   # Verde olivo
    'linea 4': '#00A6C7',   # Cian
    'linea 5': '#F9D616',   # Amarillo
    'linea 6': '#DA1C2C',   # Rojo
    'linea 7': '#F47920',   # Naranja
    'linea 8': '#179848',   # Verde bandera
    'linea 9': '#633517',   # Café
    'linea a': '#A22281',   # Morado
    'linea b': '#6BA547',   # Verde con gris
    'linea 12': '#C09200'   # Oro
}

# Mapear los colores en el orden correcto de los datos
colores = [colores_linea.get(linea, '#CCCCCC') for linea in pie_data.index]

plt.figure(figsize=(12,12))
plt.pie(
    pie_data.values,
    labels=pie_data.index,
    colors=colores,  # Añadido: colores oficiales del Metro
    autopct='%1.1f%%',
    startangle=90,
    wedgeprops={'edgecolor': 'white', 'linewidth': 1},  # Bordes blancos
    textprops={'fontsize': 12, 'fontweight': 'bold'},  # Estilo del texto
    shadow=True  # Sombra para efecto 3D
)

plt.title('Afluencia en millones de personas por línea 2022-2025', fontweight='bold')
plt.axis('equal')  
plt.show()

# %%

# Agrupar por línea
bar_data = af_linea.groupby('linea')['afluencia'].sum().sort_values(ascending=False)

# Calcular porcentajes
total = bar_data.sum()
porcentajes = (bar_data / total) * 100

# Colores oficiales del Metro CDMX
colores_linea = {
    'linea 1': '#ED2D8C',
    'linea 2': '#005DAA',
    'linea 3': '#7A8727',
    'linea 4': '#00A6C7',
    'linea 5': '#F9D616',
    'linea 6': '#DA1C2C',
    'linea 7': '#F47920',
    'linea 8': '#179848',
    'linea 9': '#633517',
    'linea a': '#A22281',
    'linea b': '#6BA547',
    'linea 12': '#C09200'
}

# Asignar colores
colores = [colores_linea.get(linea, '#CCCCCC') for linea in bar_data.index]

plt.figure(figsize=(15, 9))

bars = plt.bar(
    bar_data.index,
    bar_data.values,
    color=colores,
    edgecolor='black',
    linewidth=1.2
)

# Etiquetas con valor y porcentaje
for bar, valor, pct in zip(bars, bar_data.values, porcentajes):
    altura = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        altura,
        f'{valor:,.0f}\n({pct:.1f}%)',
        ha='center',
        va='bottom',
        fontsize=10,
        fontweight='bold'
    )

plt.title(
    'Afluencia por Línea del Metro CDMX (2022-2025)',
    fontsize=18,
    fontweight='bold'
)

plt.xlabel('Línea', fontsize=14, fontweight='bold')
plt.ylabel('Afluencia Total', fontsize=14, fontweight='bold')

plt.xticks(rotation=45, fontsize=12)
plt.yticks(fontsize=12)

plt.grid(axis='y', linestyle='--', alpha=0.4)
plt.tight_layout()
plt.show()

# %% [markdown]
# A continuación se desglosa la afluencia total del periodo 2022-2026 en función de cada línea dividido por estación correspondiente a dicha línea.
#
# De esta gráfica podemos notar el siguiente top de estaciones mas afluenciadas por línea:
#
# 1. Línea 1:
#     1. Chapultepec
#     2. Merced
#     3. Insurgentes
#     4. Pantitlán
# 2. Línea 2:
#     1. Cuatro caminos
#     2. Tasqueña
#     3. Zocalo / Tenochtitlan
# 3. Línea 3:
#     1. Indios Verdes
#     2. Universidad
#     3. Copilco
# 4. Línea 4:
#     1. Martin Carrera
#     2. Candelaria
#     3. Fray Servando
# 5. Línea 5:
#     1. Pantitlán
#     2. Politecnico
#     3. Autobuses del norte
#     4. Puerto áereo
# 6. Línea 6:
#     1. Martin carrera
#     2. Ferreria / Arena CDMX
#     3. Lindavista
#     4. El rosario
# 7. Línea 7:
#     1. Barranca del Muerto
#     2. Polanco
#     3. Audítorio
#     4. El rosario
# 8. Línea 8
#     1. Constitución de 1917
#     2. San Juan de Letrán
#     3. Coyuya
#     4. UAM
# 9. Línea 9:
#     1. Tacubaya
#     2. Pantitlán
#     3. Chilpancingo
# 10. Línea a:
#     1. La paz
#     2. Santa Marta
#     3. Pantitlán
# 11. Línea b:
#     1. Buenavista
#     2. Ciudad Azteca
#     3. Mezquis
# 12. Línea 12:
#     1. Tlahuac
#     2. Periferico Oriente
#     3. Insurgentes Sur

# %%
df_agrupado = metro.groupby(['linea', 'estacion'])['afluencia'].sum().reset_index()

# 2. Obtenemos la lista de todas las líneas únicas para iterar sobre ellas
lineas = sorted(df_agrupado['linea'].unique())

# 3. Ciclo para generar una gráfica de barras por cada línea
for linea in lineas:
    # Filtramos los datos solo para la línea actual y ordenamos alfabéticamente por estación
    data_linea = df_agrupado[df_agrupado['linea'] == linea].sort_values('estacion')
    
    plt.figure(figsize=(15, 7))
    
    # Creamos la gráfica de barras
    # Usamos un gradiente de color (palette) para que sea visualmente atractivo
    barplot = sns.barplot(
        data=data_linea, 
        x='estacion', 
        y='afluencia', 
        palette='magma',
        edgecolor='black'
    )
    
    # --- Configuración estética (basada en tu estilo previo) ---
    plt.title(f'Afluencia Total por Estación: {linea}\nPeriodo 2022 - 2026 (Datos parciales 2026)', 
              fontsize=16, fontweight='bold', pad=20)
    
    plt.xlabel('Estaciones', fontsize=12, fontweight='bold')
    plt.ylabel('Afluencia Total', fontsize=12, fontweight='bold')
    
    plt.xticks(rotation=45, ha='right', fontsize=10)
    
    # Opcional: Si los números son muy grandes, puedes formatear el eje Y 
    # para que se lea en millones o use comas
    plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: "{:,}".format(int(x))))
    
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    plt.show()

# %% [markdown]
# En el gráfico de afluencia por tipo de pago podemos ver como practicamente en el 2025 desapareció la modalidad del boleto en toda la red del metro, por lo que esta información no es reelevante para modelos de series de tiempo porque es indiferente el metodo usado para transladarse ya que lo que nos importa es la afluencia

# %%
plt.figure(figsize=(50, 50))
ax = sns.catplot(x = 'linea',
            y = 'afluencia',
            data = af_linea, 
            kind='bar', 
            hue='tipo_pago',
            row='año',
            palette= 'tab10',
            height= 9,
            aspect=1,
            errorbar= None
            )


títulos = [ 'Año 2022', 'Año 2023', 'Año 2024', 'Año 2025', 'Año 2026']  

# Iterar y agregar títulos
for i,j in enumerate(ax.axes.flat):
    # Personalizar ticks
    j.tick_params(axis='y', labelsize=12)
    j.tick_params(axis='x', labelsize=12, rotation=45)
    j.set_ylabel('Afluencia', fontsize= 12, fontweight='bold')
    j.set_xlabel('Linea', fontsize= 12, fontweight='bold')
    j.set_title(f'{títulos[i]} Afluencia en Millones por tipo de pago', fontsize=15, fontweight='bold', pad=15)
    j.grid(True)
plt.show()

# %% [markdown]
# De la siguiente gráfica de distribución de la afluencia acumulada del 2022-2026 podemos notar lo siguiente:
# Los outliers superiores (los puntos que llegan a los 30M) no son errores; son las estaciones "ancla" del sistema (como Pantitlán, Indios Verdes o Cuatro Caminos).
#
# Podemos notar que la red del Metro es altamente dependiente de menos del 5% de sus estaciones. Si una de estas estaciones de "30 millones" falla, el impacto sistémico es masivo, a diferencia de las estaciones que están dentro de la "caja" (el promedio).

# %%
plt.figure(figsize=(12,8))

sns.boxplot(
    data=af_linea,
    x='linea',
    y='afluencia',
    palette=colores_linea
)

plt.title('Distribución de afluencia por línea (2022-2026)', fontweight='bold')
plt.xlabel('Línea')
plt.ylabel('Afluencia')

plt.show()

# %% [markdown]
# El siguiente gráfico de distribución diaria por línea muestra el comportamiento diario normal de la afluencia en cada una de las líneas del sistema del metro, esto nos será muy relevante mas adelante

# %%
# 1. Agrupamos por FECHA y LINEA para tener el total diario por línea
af_diaria_linea = df_sin_index.groupby(['fecha', 'linea'])['afluencia'].sum().reset_index()

# 2. Ahora sí, generamos el boxplot con DATOS DIARIOS
plt.figure(figsize=(12,8))
sns.boxplot(
    data=af_diaria_linea,
    x='linea',
    y='afluencia',
    palette='Set3'
)

plt.title('Distribución de Afluencia DIARIA por línea (2022-2026)', fontweight='bold')
plt.xlabel('Línea')
plt.ylabel('Pasajeros por día') # La escala ahora será de miles, no millones
plt.show()

# %% [markdown]
# ## Mapa de calor

# %% [markdown]
# El siguiente mapa de calor se realizó con la intención de ver meses más afluenciados y se nota que octubre y noviembre son unos de los meses con mayor afluencia, especialmente en 2025 se nota el crecimiento en la alfuencia

# %%
af_dia['mes'] = af_dia['fecha'].dt.month
af_dia['año'] = af_dia['fecha'].dt.year

tabla = af_dia.pivot_table(
    values='afluencia',
    index='mes',
    columns='año'
)

sns.heatmap(tabla, cmap='viridis')
plt.title('Patrones de afluencia por mes y año')
plt.show()

# %% [markdown]
# *La matriz de correlación muestran poca correlación si acaso se nota un pequeño grado de correlación entre pares de años consecutivos y esto es por la tendencia que va incrementando cada año*

# %%
df = metro[metro['anio'].between(2021, 2026)]

df_diario = df.groupby(['fecha', 'anio'])['afluencia'].sum().reset_index()
df_diario['dayofyear'] = df_diario['fecha'].dt.dayofyear


df_pivot = df_diario.pivot(
    index='dayofyear',
    columns='anio',
    values='afluencia'
)
corr_matrix = df_pivot.corr()
print(corr_matrix)

plt.figure()
plt.imshow(corr_matrix)
plt.colorbar()

plt.xticks(range(len(corr_matrix.columns)), corr_matrix.columns)
plt.yticks(range(len(corr_matrix.columns)), corr_matrix.columns)

plt.title("Correlación de Afluencia entre Años")
plt.tight_layout()
plt.show()


# %%
# Calcular suma total y promedio diario por estación
top10_estaciones = (af_dia_est.groupby(['linea', 'estacion'])
                    .agg(
                        suma_total=('afluencia', 'sum'),
                        promedio_diario=('afluencia', 'mean')
                    )
                    .round(2)
                    .sort_values('promedio_diario', ascending=False)
                    .head(10))

print("Top 10 estaciones - Suma total y promedio diario:")
print(top10_estaciones)

# %% [markdown]
# La siguiente gráfica muestra el top 10 promedio diario de afluencia por estaciones de cada línea, debemos tener en cuenta que está contemplado por cada estación perteneciente a una línea, no es el promedio acumulado de una sola estación que tiene transbordes y pertenece a diferentes líneas. Se toma individualmente estación que pertenece a una línea.

# %%
import matplotlib.pyplot as plt
import seaborn as sns

# Preparar datos para visualización
top10_viz = (
    af_dia_est.groupby(['linea', 'estacion'])
    .agg(
        suma_total=('afluencia', 'sum'),
        promedio_diario=('afluencia', 'mean')
    )
    .round(2)
    .sort_values('promedio_diario', ascending=False)
    .head(10)
    .reset_index()
)

# Crear gráfico
fig, ax = plt.subplots(figsize=(15, 7))

sns.barplot(
    data=top10_viz,
    x='promedio_diario',
    y='estacion',
    hue='linea',
    dodge=False,
    palette=colores_linea,
    ax=ax
)

ax.set_title('Top 10 - Promedio Diario de Afluencia', fontsize=16, fontweight='bold')
ax.set_xlabel('Promedio de pasajeros por día')
ax.set_ylabel('Estación')

plt.tight_layout()
plt.show()

# %% [markdown]
# La siguiente serie de tiempo muestra la afluencia total por linea del periodo 2022-2026. A partir de la misma pudimos notar lo siguiente:
# 1. Obras de Infraestructura (Líneas 1 y 12)
#
#     Línea 12 (Naranja): Se observa claramente el periodo de inactividad total en 2022 (línea en cero). A partir de inicios de 2023, se ven "escalones" de subida que corresponden a las reaperturas por tramos.
#
#     Línea 1 (Rosa): se nota la caída drástica a mediados de 2022. Esto marca el inicio del proyecto de mantenimiento. La fluctuación posterior refleja la operación parcial y el desvío de usuarios a otras rutas.
#
# 2. Estacionalidad Marcada
#     Se observa que el final de cada año (diciembre-enero), todas las líneas presentan una "V" o caída pronunciada.
#
#     Interpretación: Es el efecto de las vacaciones de invierno y la suspensión de actividades escolares/administrativas.
#
# 3. Líneas más relevantes (Líneas 2 y 3)
#     Las líneas 2 y 3 se mantienen consistentemente en la cima, rozando los 17.5M a 20M de pasajeros mensuales.
#
# 4. Líneas Estables (Líneas 4 y 6)
#     Las líneas en la parte inferior de la gráfica muestran una estabilidad casi plana.
#

# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df_monthly = metro.groupby(
    [pd.Grouper(key='fecha', freq='MS'), 'linea']
)['afluencia'].sum().reset_index()

cutoff_date = pd.to_datetime('2026-01-01')

plt.figure(figsize=(16, 8))
sns.set_style("ticks")

lineas = sorted(df_monthly['linea'].unique())

for linea in lineas:
    subset = df_monthly[df_monthly['linea'] == linea]
    historical = subset[subset['fecha'] < cutoff_date]
    current_year = subset[subset['fecha'] >= cutoff_date]

    color = colores_linea.get(linea.lower(), '#CCCCCC')

    plt.plot(
        historical['fecha'],
        historical['afluencia'],
        label=linea,
        color=color,
        linewidth=2,
        marker='o',
        markersize=4
    )

    if not current_year.empty:
        gap_connector = pd.concat([historical.tail(1), current_year])
        plt.plot(
            gap_connector['fecha'],
            gap_connector['afluencia'],
            color=color,
            linestyle='--',
            linewidth=2,
            alpha=0.7
        )

plt.axvline(cutoff_date, color='gray', linestyle=':', alpha=0.8)
plt.text(
    cutoff_date,
    plt.ylim()[1] * 0.95,
    '  Datos parciales de 2026',
    color='gray',
    fontweight='bold'
)

plt.title(
    'Afluencia mensual por línea del Metro CDMX (2022-2026)',
    fontsize=16,
    fontweight='bold'
)

plt.xlabel('Año', fontsize=12)
plt.ylabel('Afluencia', fontsize=12)

plt.gca().yaxis.set_major_formatter(
    plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M')
)

plt.legend(
    title='Líneas del Metro',
    bbox_to_anchor=(1.05, 1),
    loc='upper left'
)

plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()
