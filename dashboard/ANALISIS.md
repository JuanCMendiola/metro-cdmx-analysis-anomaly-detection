# Dashboard - notas y limitaciones

Prototipo inicial (Streamlit) para visualizar en un mapa la demanda total y
las anomalías detectadas por `modeling/modelado.ipynb`, por línea/estación.

## Fuente de las coordenadas (`estaciones_coordenadas.csv`)

El dataset de afluencia (`datos.cdmx.gob.mx`) no incluye latitud/longitud de
las estaciones. El portal de datos abiertos de la CDMX sí publica un dataset
oficial de líneas y estaciones con geometría ("Líneas y Estaciones del STC
Metro (SHP)"), pero no fue accesible desde este entorno al momento de armar
el prototipo.

En su lugar, las coordenadas de `estaciones_coordenadas.csv` se extrajeron de
un mapa Folium (`mapa_estaciones.html`) publicado en un repositorio público
de terceros en GitHub
([MarcosIsaacRodriguezMoreno/Proyecto-Final-Modulo-6](https://github.com/MarcosIsaacRodriguezMoreno/Proyecto-Final-Modulo-6)),
que a su vez las calcula promediando puntos GTFS por estación. Se
normalizaron los nombres de línea/estación con la misma función
`limpiar_texto` que usa el resto del pipeline, para poder cruzarlas por
(`linea`, `estacion`) contra `master_auditoria_consenso_MAD.csv` /
`af_modelo.pkl`. Cobertura verificada: **196/196** combinaciones
línea-estación del dataset del proyecto tienen coordenada (dos filas,
`linea 1` / `gómez farias` y `gómez farías`, corresponden a la misma
estación física con dos grafías distintas en la fuente original — ambas
quedaron con la misma coordenada).

**Pendiente / a verificar:** esta fuente es de terceros, no la oficial. Antes
de usar el dashboard para algo mas que un prototipo, conviene:
1. Conseguir el dataset oficial de `datos.cdmx.gob.mx` ("Líneas y Estaciones
   del STC Metro") y revalidar/reemplazar estas coordenadas contra él.
2. Revisar visualmente en el mapa que ninguna estación quedó mal ubicada.

## Qué necesita el dashboard para correr

- `data/processed/af_modelo.pkl` (lo genera `data/recoleccion_y_limpieza.py`
  → `eda/analisis_exploratorio.py` → `feature_engineering/feature_engineering.py`,
  o simplemente `python setup_pipeline.py`) - para la vista de demanda.
- `master_auditoria_consenso_MAD.csv` (lo genera `modeling/modelado.ipynb`) -
  para la vista de anomalías.

Si falta alguno de los dos, esa vista se deshabilita con un aviso en vez de
tronar.

## Siguientes pasos

- Reemplazar las coordenadas por la fuente oficial de la CDMX.
- Agregar más filtros (por ejemplo, tipo de hallazgo OSINT una vez cruzado
  con `bitacora_investigacion_anomalias_criticas.csv`).
- Evaluar mostrar la red como líneas (no solo puntos), coloreadas por línea
  del metro, para que se vea como un mapa real del sistema.
