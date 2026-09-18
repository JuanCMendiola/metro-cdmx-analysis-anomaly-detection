# metro-cdmx-analysis-anomaly-detection

Anomaly detection on Mexico City Metro (STC) daily ridership data: EDA, time-series feature engineering, and Prophet-based anomaly detection across ~195 line/station series, validated against a manually researched (OSINT) incident log.

## Project structure

```
data/                   Data collection and cleaning (raw + breakdown datasets)
eda/                    Exploratory data analysis
feature_engineering/    Rolling stats, ACF/PACF, STL decomposition, model-ready dataset
modeling/               Modeling notebook (SARIMAX, Prophet, anomaly detection) - active WIP
```

The project was originally a single notebook (`tt.ipynb`); finished stages (data, EDA, feature engineering) were split into plain `.py` files (percent-cell format, runnable in VS Code / Jupytext), while modeling stays a notebook since it's still under active development.

## Setup

```
pip install -r requirements.txt
```

Versions are pinned for the packages already verified in this environment (pandas, numpy, matplotlib, seaborn, plotly, openpyxl); `scikit-learn`, `statsmodels`, `pmdarima` and `prophet` are left as minimum versions. On Windows, the first `prophet` install can take a while since it pulls/builds the `cmdstan` backend via `cmdstanpy`.

## How to run

The `.py` files are **not** standalone scripts — they share in-memory variables (`metro` is reused and overwritten between files), so they must be run in the same kernel, in this exact order (not folder by folder):

1. `data/01_recoleccion_y_limpieza.py` - downloads and cleans the simple dataset (2010-2026). Creates `metro`.
2. `eda/01_eda_simple.py` - uses that (simple) `metro`. First aggregated time series.
3. `data/02_carga_dataset_desglosado.py` - downloads the breakdown dataset and **overwrites** `metro`. Creates `dataset_original_copy` and saves the checkpoint `data/processed/dataset_original_copy.pkl`.
4. `eda/02_eda_desglosado.py` - uses the breakdown `metro`. Creates `af_dia_est`. Most EDA charts are produced here.
5. `feature_engineering/01_feature_engineering.py` - rolling stats, ACF/PACF, visualization of the ~195 series with flagged anomalies.
6. `feature_engineering/02_preprocesamiento.py` - STL decomposition, filters stations with >=500 valid observations, builds `af_modelo` and saves the second checkpoint `data/processed/af_modelo.pkl`.

Run each file with "Run All" (VS Code Jupyter/Python extension) **without restarting the kernel between files**, always with the repo root as the working directory.

7. Once both `.pkl` checkpoints exist, `modeling/modelado.ipynb` can be opened and run **on its own, from a fresh kernel** - its Setup cell loads the checkpoints directly, no need to run steps 1-6 first. It walks through: single-station SARIMAX exploration, SARIMA vs Prophet comparison, anomaly-detection method comparison, then the 195-station engine (trains one Prophet per line/station, so it takes a while) producing `master_auditoria_consenso_MAD.csv`/`.xlsx`, and finally the OSINT results section using the manual investigation log.

## Current state

- Data pipeline produces two checkpoints (`data/processed/*.pkl`) so `modeling/` can load processed data directly instead of re-running the full pipeline.
- Anomaly detection is centered on one model: `motor_auditoria_consenso_mad_bidireccional`, which fits Prophet per station/line and flags anomalies by combining Prophet's confidence interval with a robust (MAD-based) z-score, across all series at once. Prophet is not trained on station-closure days (afluencia=0) so those days don't bias the learned trend, but it still predicts on them so real closures keep getting flagged as anomalies. An earlier single-station Prophet prototype and a separate LightGBM experiment were both removed in favor of this single scaled model.
- A stratified sample of critical anomalies was manually investigated (OSINT) and logged in `bitacora_investigacion_anomalias_criticas.csv`, used to validate and analyze the detected anomalies.
- Next steps under consideration: adding more regressors to Prophet, and evaluating Isolation Forest as an alternative/complementary anomaly detector.