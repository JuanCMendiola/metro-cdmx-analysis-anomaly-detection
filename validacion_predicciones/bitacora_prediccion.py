# Lectura de la bitacora OSINT de las predicciones, compartida por
# validacion_predicciones.py y estaciones_y_causas.py (asi ambos usan los mismos datos).
# La investigacion es manual; aqui solo se lee y se aplica el ajuste acordado por el equipo.
import pandas as pd

BITACORA_PRED = 'validacion_predicciones/datos/bitacora_validacion_predicciones_original.csv'   # OSINT original del equipo (79 filas)
FERIADO_AJUSTE = '2026-09-16'   # Independencia: filas "No" de este dia pasan a Parcial / Feriado
CAUSA_FERIADO = 'Feriado No Oficial / Cultural'


def leer_bitacora_pred(ruta=BITACORA_PRED, avisar=True):
    # La bitacora original viene de la hoja de calculo del equipo: fechas m/d/aaaa y afluencia con comas de miles
    df = pd.read_csv(ruta, thousands=',')
    df['Fecha'] = pd.to_datetime(df['Fecha'], format='%m/%d/%Y')
    # Unico ajuste a la bitacora original (decision del equipo, 25-nov-2026): el 16-sep es feriado,
    # asi que las filas de ese dia calificadas "No" cuentan como evento indirecto ("Parcial") y su
    # causa pasa a feriado. El CSV no se modifica; el ajuste vive solo aqui.
    feriado_no = (df['Fecha'] == FERIADO_AJUSTE) & df['Ocurrio_Evento'].str.startswith('No')
    df.loc[feriado_no, 'Ocurrio_Evento'] = 'Parcial - Evento cercano/indirecto'
    df.loc[feriado_no, 'Hallazgo_Principal'] = CAUSA_FERIADO
    if avisar:
        print(f'Ajuste feriado {FERIADO_AJUSTE}: {int(feriado_no.sum())} filas de "No" a "Parcial" con causa "{CAUSA_FERIADO}"')
    return df
