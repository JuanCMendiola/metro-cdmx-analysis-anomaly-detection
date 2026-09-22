# Prototipo de dashboard: mapa de la red del Metro CDMX con demanda total y
# anomalias detectadas por estacion. Contexto y limitaciones de los datos de
# coordenadas: ver dashboard/ANALISIS.md.
#
# Requiere que ya hayas corrido el pipeline (ver README de la raiz):
#   python setup_pipeline.py            (genera data/processed/af_modelo.pkl)
#   modeling/modelado.ipynb             (genera master_auditoria_consenso_MAD.csv)
#
# Correr con la raiz del repo como working directory:
#   streamlit run dashboard/app.py

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent
COORDS_PATH = Path(__file__).resolve().parent / "estaciones_coordenadas.csv"
AF_MODELO_PATH = REPO_ROOT / "data" / "processed" / "af_modelo.pkl"
MASTER_AUDITORIA_PATH = REPO_ROOT / "master_auditoria_consenso_MAD.csv"

st.set_page_config(page_title="Metro CDMX - Demanda y anomalias", layout="wide")


@st.cache_data
def cargar_coordenadas():
    return pd.read_csv(COORDS_PATH)


@st.cache_data
def cargar_demanda():
    if not AF_MODELO_PATH.exists():
        return None
    af_modelo = pd.read_pickle(AF_MODELO_PATH)
    demanda = (
        af_modelo.groupby(["linea", "estacion"])["afluencia"]
        .sum()
        .reset_index()
        .rename(columns={"afluencia": "afluencia_total"})
    )
    return demanda


@st.cache_data
def cargar_anomalias():
    if not MASTER_AUDITORIA_PATH.exists():
        return None
    df = pd.read_csv(MASTER_AUDITORIA_PATH)
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df


coords = cargar_coordenadas()
demanda = cargar_demanda()
anomalias = cargar_anomalias()

st.title("Metro CDMX: demanda y anomalias por estacion")
st.caption(
    "Prototipo. Coordenadas de estaciones extraidas de una fuente de "
    "terceros, no verificadas contra el dataset oficial de la CDMX - ver "
    "dashboard/ANALISIS.md."
)

if demanda is None and anomalias is None:
    st.error(
        "No se encontraron data/processed/af_modelo.pkl ni "
        "master_auditoria_consenso_MAD.csv. Corre 'python setup_pipeline.py' "
        "y despues modeling/modelado.ipynb (ver README)."
    )
    st.stop()

vista = st.sidebar.radio("Vista", ["Demanda total", "Anomalias"])

if vista == "Demanda total":
    if demanda is None:
        st.warning(
            "Falta data/processed/af_modelo.pkl. Corre "
            "'python setup_pipeline.py' primero."
        )
        st.stop()

    df_mapa = demanda.merge(coords, on=["linea", "estacion"], how="inner")
    sin_coords = len(demanda) - len(df_mapa)
    if sin_coords:
        st.caption(f"{sin_coords} estaciones sin coordenada no se muestran en el mapa.")

    lineas_disp = sorted(df_mapa["linea"].unique())
    lineas_sel = st.sidebar.multiselect("Lineas", lineas_disp, default=lineas_disp)
    df_mapa = df_mapa[df_mapa["linea"].isin(lineas_sel)]

    fig = px.scatter_mapbox(
        df_mapa,
        lat="lat",
        lon="lon",
        size="afluencia_total",
        color="linea",
        hover_name="estacion",
        hover_data={"afluencia_total": ":,", "lat": False, "lon": False, "linea": True},
        zoom=10,
        height=700,
        mapbox_style="open-street-map",
        title="Afluencia total acumulada por estacion",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig, width='stretch')

    st.subheader("Top 15 estaciones por afluencia total")
    st.dataframe(
        df_mapa[["linea", "estacion", "afluencia_total"]]
        .sort_values("afluencia_total", ascending=False)
        .head(15)
        .reset_index(drop=True)
    )

else:
    if anomalias is None:
        st.warning(
            "Falta master_auditoria_consenso_MAD.csv. Corre "
            "modeling/modelado.ipynb primero."
        )
        st.stop()

    prioridades = sorted(anomalias["prioridad_auditoria"].unique())
    prioridades_sel = st.sidebar.multiselect(
        "Prioridad de la anomalia", prioridades, default=prioridades
    )

    fecha_min, fecha_max = anomalias["fecha"].min(), anomalias["fecha"].max()
    rango_fechas = st.sidebar.date_input(
        "Rango de fechas",
        (fecha_min, fecha_max),
        min_value=fecha_min,
        max_value=fecha_max,
    )

    df_filtrado = anomalias[anomalias["prioridad_auditoria"].isin(prioridades_sel)]
    if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
        inicio, fin = pd.Timestamp(rango_fechas[0]), pd.Timestamp(rango_fechas[1])
        df_filtrado = df_filtrado[
            (df_filtrado["fecha"] >= inicio) & (df_filtrado["fecha"] <= fin)
        ]

    resumen = (
        df_filtrado.groupby(["linea", "estacion"])
        .agg(
            total_anomalias=("prioridad_auditoria", "count"),
            impacto_promedio=("impacto_pasajeros", "mean"),
        )
        .reset_index()
    )
    df_mapa = resumen.merge(coords, on=["linea", "estacion"], how="inner")

    if df_mapa.empty:
        st.info("No hay anomalias para los filtros seleccionados.")
    else:
        fig = px.scatter_mapbox(
            df_mapa,
            lat="lat",
            lon="lon",
            size="total_anomalias",
            color="impacto_promedio",
            color_continuous_scale="RdBu",
            hover_name="estacion",
            hover_data={
                "total_anomalias": True,
                "impacto_promedio": ":.0f",
                "lat": False,
                "lon": False,
            },
            zoom=10,
            height=700,
            mapbox_style="open-street-map",
            title="Anomalias detectadas por estacion (tamano = cantidad, color = impacto promedio)",
        )
        fig.update_layout(margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, width='stretch')

    st.subheader(f"Detalle ({len(df_filtrado):,} anomalias en el filtro actual)")
    st.dataframe(
        df_filtrado.sort_values("fecha", ascending=False)
        .head(200)[
            ["fecha", "linea", "estacion", "prioridad_auditoria",
             "direccion_anomalia", "impacto_pasajeros"]
        ]
        .reset_index(drop=True)
    )
