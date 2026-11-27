# %% [markdown]
# Version para presentacion de la grafica 04 (afluencia real por nivel de riesgo).
# Compara directamente un dia cualquiera (~3%) contra los dias en alerta, para que
# la diapositiva se entienda sola. Usa la tabla que ya genera validacion_predicciones.py,
# asi que no recalcula nada: correr primero ese script si cambian los datos.
# Ejecutar desde la raiz del repo:
#   python validacion_predicciones/grafica_afluencia_real_presentacion.py

# %%
import os
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

CARPETA = 'validacion_predicciones'
TABLA = f'{CARPETA}/resultados/tasas_afluencia_real_por_estrato.csv'
SALIDA = f'{CARPETA}/img/04b_afluencia_real_vs_dia_cualquiera.png'
TASA_HISTORICA = 3.0   # % de estacion-dias CRITICOS en el historico (igual que validacion_predicciones.py)

TINTA, TINTA2, FONDO, REJILLA = '#0b0b0b', '#52514e', '#fcfcfb', '#e4e3df'
AZUL, AZUL_OSCURO, AZUL_CLARO, GRIS, NARANJA = '#2a78d6', '#1a4f8f', '#9ec5f4', '#b5b4ae', '#eb6834'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'figure.facecolor': FONDO, 'axes.facecolor': FONDO,
                     'text.color': TINTA, 'axes.labelcolor': TINTA2, 'xtick.color': TINTA2, 'ytick.color': TINTA})

t = pd.read_csv(TABLA, encoding='utf-8-sig').set_index('estrato')

def fila(clave):
    r = t.loc[clave]
    c, n = int(r['criticas']), int(r['dias_en_alerta'])
    return c, n, c / n * 100          # sin el redondeo de la tabla (31/230 = 13.48%)

c_tot, n_tot, p_tot = fila('Todos los dias en alerta')
c_a, n_a, p_a = fila('A - Alta')
c_b, n_b, p_b = fila('B - Media')
c_c, n_c, p_c = fila('C - Control')

def veces(p):
    v = round(p / TASA_HISTORICA)
    return f'unas {v} veces más' if v > 1 else 'igual'

# (etiqueta, detalle, %, color, nota a la derecha)
filas = [
    ('Un día cualquiera', 'referencia histórica', TASA_HISTORICA, GRIS, ''),
    ('Días que marcó el modelo', f'{n_tot} estación-días', p_tot, AZUL_OSCURO, veces(p_tot)),
    (None, None, None, None, None),   # separador
    ('Riesgo alto', f'{c_a} de {n_a}, todos el 16 de septiembre', p_a, AZUL, veces(p_a)),
    ('Riesgo medio', f'{c_b} de {n_b}', p_b, AZUL_CLARO, veces(p_b)),
    ('Riesgo bajo', f'{c_c} de {n_c}', p_c, AZUL_CLARO, veces(p_c)),
]

fig, ax = plt.subplots(figsize=(13, 7.2))
y = 0
pos = []
for etiqueta, detalle, p, color, nota in filas:
    if etiqueta is None:
        y -= 0.55
        ax.text(-0.6, y + 0.05, 'Por nivel de riesgo que dio el modelo:', ha='right', va='center',
                fontsize=12, color=TINTA2, style='italic')
        y -= 0.75
        continue
    grande = etiqueta in ('Un día cualquiera', 'Días que marcó el modelo')
    ax.barh(y, p, height=0.66 if grande else 0.56, color=color)
    ax.text(-0.6, y + 0.13, etiqueta, ha='right', va='center', fontsize=15 if grande else 13,
            fontweight='bold' if grande else 'normal')
    ax.text(-0.6, y - 0.2, detalle, ha='right', va='center', fontsize=10.5, color=TINTA2)
    ax.text(p + 0.6, y, f'{p:.0f}%', ha='left', va='center', fontsize=20 if grande else 16, fontweight='bold')
    if nota:
        ax.text(p + (5.2 if p >= 10 else 4.4), y, nota, ha='left', va='center',
                fontsize=13 if grande else 11.5, color=NARANJA if grande else TINTA2,
                fontweight='bold' if grande else 'normal')
    pos.append(y)
    y -= 1.1

# Linea de referencia del 3% en todas las barras
ax.plot([TASA_HISTORICA] * 2, [min(pos) - 0.45, max(pos) + 0.45], color=NARANJA, linestyle='--', linewidth=1.8, zorder=0)

ax.set_xlim(0, 50)
ax.set_ylim(min(pos) - 0.6, max(pos) + 0.6)
ax.set_yticks([]); ax.set_xticks([])
for s in ax.spines.values(): s.set_visible(False)

fig.suptitle(f'En los días que marcó el modelo, la afluencia anormal fue {veces(p_tot)} frecuente',
             fontsize=18, fontweight='bold', x=0.02, ha='left', y=0.965)
fig.text(0.02, 0.875, 'De cada 100 estación-días, ¿cuántos tuvieron afluencia anormal según los datos reales de SEMOVI?',
         fontsize=12.5, color=TINTA2)
fig.text(0.02, 0.03,
         'Afluencia anormal = anomalía crítica en la afluencia diaria real (2 de agosto al 30 de septiembre de 2026). '
         'Línea naranja: un día cualquiera, ~3%.\n'
         'Riesgo alto = 10% de días en alerta con mayor probabilidad; medio = siguiente 15%; bajo = el resto. '
         'Fuente: SEMOVI (datos.cdmx.gob.mx).',
         fontsize=9.5, color=TINTA2, va='bottom')
fig.subplots_adjust(left=0.30, right=0.98, top=0.83, bottom=0.12)
fig.savefig(SALIDA, dpi=200)
print(f'Gráfica guardada en {SALIDA}')
