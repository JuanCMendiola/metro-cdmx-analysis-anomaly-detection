# %%
# EDA sobre el dataset simple y el dataset desglosado.
# Fusion de los antiguos eda/01_eda_simple.py + eda/02_eda_desglosado.py.
# Las notas/markdown que acompanaban este codigo estan en ANALISIS.md (esta misma carpeta).
# Cada grafica se guarda en eda/img/ ademas de mostrarse (plt.show()).

# Carpeta donde se guardan las graficas del EDA conforme se van generando.
import os
os.makedirs('eda/img', exist_ok=True)

# %%
af_dia = metro_simple.groupby('fecha')['afluencia'].sum()
af_dia.to_frame()
af_dia = af_dia.reset_index()
af_dia

# %%
# Agrupar por fecha para ver la demanda total del sistema
ts_data = metro_simple.groupby('fecha')['afluencia'].sum().reset_index()

plt.figure(figsize=(15, 6))
plt.plot(ts_data['fecha'], ts_data['afluencia'], label='Afluencia Diaria')
# Media móvil de 7 días para suavizar la serie
ts_data['rolling_7d'] = ts_data['afluencia'].rolling(window=7).mean()
plt.plot(ts_data['fecha'], ts_data['rolling_7d'], color='red', label='Media Móvil (7 días)')

plt.title('Evolución de la Afluencia del Metro en el Tiempo')
plt.xlabel('Fecha')
plt.ylabel('Pasajeros')
plt.legend()
plt.savefig('eda/img/01_evolucion_afluencia_2010-2026.png', dpi=150, bbox_inches='tight')
plt.show()

print(round(af_dia['afluencia'].describe(),2))

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

# %%
#el dataset ya no es muy grande, por lo que ahora si se puede guardar como excel
#metro.to_excel('metro_limpio.xlsx', index= False)

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
plt.savefig('eda/img/02_evolucion_afluencia_2022-2026.png', dpi=150, bbox_inches='tight')
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

# %%
#pie chart de la afluencia total por año a partir del 2022 al 2026
af_anual = df_sin_index.groupby('año')['afluencia'].sum().reset_index()
af_anual = af_anual[af_anual['año'] < 2026]
plt.figure(figsize=(8, 8))
plt.pie(af_anual['afluencia'], labels=af_anual['año'], autopct='%1.1f%%', startangle=140)
plt.title('Distribución de Afluencia Total por Año (2022-2025)', fontweight='bold')
plt.savefig('eda/img/03_pie_afluencia_anual.png', dpi=150, bbox_inches='tight')
plt.show()

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
plt.savefig('eda/img/04_pie_afluencia_por_linea.png', dpi=150, bbox_inches='tight')
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
plt.savefig('eda/img/05_barras_afluencia_por_linea.png', dpi=150, bbox_inches='tight')
plt.show()

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
    
    plt.savefig(f'eda/img/06_barras_estacion_{linea.replace(" ", "_")}.png', dpi=150, bbox_inches='tight')
    plt.show()

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
ax.savefig('eda/img/07_afluencia_tipo_pago_por_anio.png', dpi=150, bbox_inches='tight')
plt.show()

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

plt.savefig('eda/img/08_boxplot_afluencia_por_linea.png', dpi=150, bbox_inches='tight')
plt.show()

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
plt.savefig('eda/img/09_boxplot_afluencia_diaria_por_linea.png', dpi=150, bbox_inches='tight')
plt.show()

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
plt.savefig('eda/img/10_heatmap_afluencia_mes_anio.png', dpi=150, bbox_inches='tight')
plt.show()

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
plt.savefig('eda/img/11_correlacion_afluencia_entre_anios.png', dpi=150, bbox_inches='tight')
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
plt.savefig('eda/img/12_top10_promedio_diario.png', dpi=150, bbox_inches='tight')
plt.show()

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
plt.savefig('eda/img/13_afluencia_mensual_por_linea.png', dpi=150, bbox_inches='tight')
plt.show()
