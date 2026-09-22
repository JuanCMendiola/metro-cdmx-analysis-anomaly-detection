# metro-cdmx-analysis-anomaly-detection

Anomaly detection on Mexico City Metro (STC) daily ridership data: EDA, time-series feature engineering, and Prophet-based anomaly detection across ~195 line/station series, validated against a manually researched (OSINT) incident log.

## Project structure

```
data/                   Data collection and cleaning (raw + breakdown datasets)
eda/                    Exploratory data analysis (+ eda/img/, saved charts)
feature_engineering/    Rolling stats, ACF/PACF, STL decomposition, model-ready dataset
modeling/               Modeling notebook (SARIMAX, Prophet, anomaly detection) - active WIP
```

The project was originally a single notebook (`tt.ipynb`); it was split into one plain `.py` file per stage (percent-cell format, runnable in VS Code / Jupytext), one per folder below. The narrative/markdown commentary that used to sit next to that code (findings, interpretations) now lives in an `ANALISIS.md` inside each of `data/`, `eda/` and `feature_engineering/`, next to that stage's `.py` file, so the `.py` files only contain code. `modeling/` stays a notebook since it's still under active development.

## Setup

```
pip install -r requirements.txt
```

Versions are pinned for the packages already verified in this environment (pandas, numpy, matplotlib, seaborn, plotly, openpyxl); `scikit-learn`, `statsmodels`, `pmdarima` and `prophet` are left as minimum versions. On Windows, the first `prophet` install can take a while since it pulls/builds the `cmdstan` backend via `cmdstanpy`.

## How to run

The `.py` files are **not** standalone scripts — they share in-memory variables (`metro`/`metro_simple` are created by the first file and consumed by the next ones), so they must be run in the same kernel, in this exact order:

1. `data/recoleccion_y_limpieza.py` - downloads and cleans the simple dataset (2010-2026), snapshots it as `metro_simple`, then downloads and cleans the breakdown dataset into `metro` (**overwriting** the simple one). Creates `dataset_original_copy` and saves the checkpoint `data/processed/dataset_original_copy.pkl`.
2. `eda/analisis_exploratorio.py` - first half uses `metro_simple` (full 2010-2026 history, incl. the pandemic dip); second half uses the breakdown `metro`, creates `af_dia_est`, and produces most EDA charts. Every chart is saved to `eda/img/` (via `plt.savefig`, e.g. `eda/img/01_evolucion_afluencia_2010-2026.png`) in addition to being shown with `plt.show()`, so you can browse the results afterwards without re-running the script.
3. `feature_engineering/feature_engineering.py` - rolling stats, ACF/PACF, visualization of anomalies, STL decomposition, filters stations with >=500 valid observations, builds `af_modelo` and saves the second checkpoint `data/processed/af_modelo.pkl`.

Run each file with "Run All" (VS Code Jupyter/Python extension) **without restarting the kernel between files**, always with the repo root as the working directory. The first code cell of `data/recoleccion_y_limpieza.py` (commented out) installs `requirements.txt` if needed.

4. Once both `.pkl` checkpoints exist, `modeling/modelado.ipynb` can be opened and run **on its own, from a fresh kernel** - its Setup cell loads the checkpoints directly, no need to run steps 1-3 first. It walks through: single-station SARIMAX exploration, SARIMA vs Prophet comparison, anomaly-detection method comparison, then the 195-station engine (trains one Prophet per line/station, so it takes a while) producing `master_auditoria_consenso_MAD.csv`/`.xlsx`, and finally the OSINT results section using the manual investigation log.

## Current state

- Data pipeline produces two checkpoints (`data/processed/*.pkl`) so `modeling/` can load processed data directly instead of re-running the full pipeline.
- Anomaly detection is centered on one model: `motor_auditoria_consenso_mad_bidireccional`, which fits Prophet per station/line and flags anomalies by combining Prophet's confidence interval with a robust (MAD-based) z-score, across all series at once. Prophet is not trained on station-closure days (afluencia=0) so those days don't bias the learned trend, but it still predicts on them so real closures keep getting flagged as anomalies. An earlier single-station Prophet prototype and a separate LightGBM experiment were both removed in favor of this single scaled model.
- A stratified sample of critical anomalies was manually investigated (OSINT) and logged in `bitacora_investigacion_anomalias_criticas.csv`, used to validate and analyze the detected anomalies.
- Next steps under consideration: adding more regressors to Prophet, and evaluating Isolation Forest as an alternative/complementary anomaly detector.