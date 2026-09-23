# metro-cdmx-analysis-anomaly-detection

Anomaly detection on Mexico City Metro (STC) daily ridership data: EDA, time-series feature engineering, and Prophet-based anomaly detection across ~195 line/station series, validated against a manually researched (OSINT) incident log.

## Project structure

```
data/                   Data collection and cleaning (raw + breakdown datasets)
eda/                    Exploratory data analysis (+ eda/img/, saved charts)
feature_engineering/    Rolling stats, ACF/PACF, STL decomposition, model-ready dataset (+ feature_engineering/img/, saved charts)
modeling/               Prophet modeling notebook (active WIP) + sarima_backup.py (archived SARIMA/SARIMAX exploration)
dashboard/              Streamlit prototype: map of demand/anomalies per station - active WIP
```

Each of `data/`, `eda/` and `feature_engineering/` is a single plain `.py` file (percent-cell format, runnable in VS Code / Jupytext) plus an `ANALISIS.md` with that stage's notes/findings. See "What changed from the original notebook" below for the full picture.

## Setup

```
pip install -r requirements.txt
```

Versions are pinned for the packages already verified in this environment (pandas, numpy, matplotlib, seaborn, plotly, openpyxl); `scikit-learn`, `statsmodels`, `pmdarima` and `prophet` are left as minimum versions. On Windows, the first `prophet` install can take a while since it pulls/builds the `cmdstan` backend via `cmdstanpy`.

## How to run

**Quickest path (after cloning):**

```
python setup_pipeline.py
```

This runs `data/recoleccion_y_limpieza.py` -> `eda/analisis_exploratorio.py` -> `feature_engineering/feature_engineering.py` in order (each as its own process), leaving all four checkpoints in `data/processed/*.pkl` and all the EDA/feature-engineering charts saved. Run it once with the repo root as the working directory (and stop if any step errors out). After that, just open `modeling/modelado.ipynb`.

**Running a stage on its own:** each `.py` file is also self-contained - it only imports what it actually needs, and instead of relying on variables left over in memory by a previous script, it loads its inputs from the `data/processed/*.pkl` checkpoint(s) saved by the previous stage. That means any file can be run by itself — "Run All" (VS Code Jupyter/Python extension) or `python <file>.py` — from a **fresh kernel/process**, with the repo root as the working directory. They still have to run in this order at least once (`setup_pipeline.py` already does this for you), because each one's checkpoint is the next one's input:

1. `data/recoleccion_y_limpieza.py` - downloads and cleans the simple dataset (2010-2026) and saves it as the checkpoint `data/processed/metro_simple.pkl`, then downloads and cleans the breakdown dataset and saves `dataset_original_copy` as `data/processed/dataset_original_copy.pkl`.
2. `eda/analisis_exploratorio.py` - loads both checkpoints from step 1. First half uses `metro_simple` (full 2010-2026 history, incl. the pandemic dip); second half uses the breakdown dataset, creates `af_dia_est`, and produces most EDA charts. Every chart is saved to `eda/img/` (via `plt.savefig`, e.g. `eda/img/01_evolucion_afluencia_2010-2026.png`) in addition to being shown with `plt.show()`, so you can browse the results afterwards without re-running the script. Saves `af_dia_est` as the checkpoint `data/processed/af_dia_est.pkl`.
3. `feature_engineering/feature_engineering.py` - loads `af_dia_est` from step 2's checkpoint. Rolling stats, ACF/PACF, visualization of anomalies, STL decomposition, filters stations with >=500 valid observations, builds `af_modelo` and saves it as the checkpoint `data/processed/af_modelo.pkl`. Like the EDA script, its charts are saved to `feature_engineering/img/` in addition to `plt.show()`.

4. Once both `dataset_original_copy.pkl` and `af_modelo.pkl` exist, `modeling/modelado.ipynb` can be opened and run on its own - its Setup cell loads those checkpoints directly, no need to run steps 1-3 first if they already exist. It walks through: single-station Prophet exploration on a train/test split, anomaly-detection method comparison (MAD residuals vs Prophet's confidence interval), then the 195-station engine (trains one Prophet per line/station, so it takes a while) producing `master_auditoria_consenso_MAD.csv`/`.xlsx`, and finally the OSINT results section using the manual investigation log. The 195-station engine also saves one forecast chart per series (full history + last-90-days zoom + 30-day Prophet forecast) to `modeling/img_pronosticos/<linea>/<estacion>.png`, and stores every series' Prophet forecast (history + next days) in `data/processed/prophet_series.pkl`. The last section of the notebook continues from those forecasts: a Random Forest / XGBoost classifier takes Prophet's outputs (expected level and interval width) plus calendar features and estimates, for each future station-day, the probability of a CRITICAL anomaly, writing `propuesta_anomalias_futuras.csv` (Prophet forecast + risk per station-day). Features also include Prophet's holiday/yearly components, seasonal weather proxies, OSINT-derived non-official holidays and per-station demand traits; day-of-week is deliberately excluded/balanced so the model does not just learn that weekends are risky. It is validated with a temporal split (also within each weekday) against references and a no-Prophet ablation; it ranks days/stations to watch, it does not confirm incidents. Details, numbers and limitations: `modeling/ANALISIS.md`. The earlier single-station SARIMA/SARIMAX exploration (and the SARIMA side of the SARIMA-vs-Prophet comparison) was archived, unmodified, to `modeling/sarima_backup.py` - it's no longer part of the active notebook. That file follows the same self-contained `.py` pattern as `data/`, `eda/` and `feature_engineering/` (loads `af_modelo.pkl`, non-blocking `Agg` backend, saves its charts to `modeling/img_sarima_backup/`).

**Important (VS Code):** open the repo root folder (`metro-cdmx-analysis-anomaly-detection`, the one with this `README.md`) in VS Code, not a subfolder like `modeling/` - relative paths like `data/processed/...` are resolved from whatever folder VS Code treats as the working directory (for `.py` files that's normally the opened folder; for a notebook's Jupyter kernel it can default to the notebook's own folder instead, which is why `modelado.ipynb`'s Setup cell `chdir`s up a level if it detects it started inside `modeling/`).

5. Once `master_auditoria_consenso_MAD.csv` exists (from step 4) - and ideally `af_modelo.pkl` too, for the demand view - the dashboard prototype can be started with:

   ```
   streamlit run dashboard/app.py
   ```

   It's a first pass at mapping the network: a "Demanda total" view (bubble map sized by accumulated ridership per station) and an "Anomalias" view (bubble map sized by anomaly count, colored by average impact, with line/priority/date filters). See `dashboard/ANALISIS.md` for where the station coordinates came from and their current limitations (they're from a third-party source, not yet validated against the CDMX government's official station geometry dataset).

## What changed from the original notebook

The project started as a single notebook (`tt.ipynb`). Since then:

- **Split by stage, one file per folder.** `data/`, `eda/` and `feature_engineering/` each hold a single plain `.py` file (percent-cell format, `# %%`) instead of a notebook. `modeling/modelado.ipynb` is the one exception and stays a notebook, since it's still being actively edited.
- **No markdown mixed into the code.** The narrative/interpretation that used to sit in markdown cells now lives in an `ANALISIS.md` inside each of `data/`, `eda/`, `feature_engineering/` and `modeling/` (for the archived SARIMA notes); the `.py` files only contain code and its normal inline comments. `modelado.ipynb` keeps its own markdown cells natively, since it's a notebook.
- **Self-contained stages, no shared kernel.** Each stage used to depend on variables left in memory by whichever script ran before it in the same kernel; now every `.py` file loads its inputs from a `data/processed/*.pkl` checkpoint and can be run on its own, in a fresh kernel/process, at any time.
- **One command to set everything up.** `python setup_pipeline.py` runs `data/` -> `eda/` -> `feature_engineering/` in order, so cloning the repo and getting to a runnable `modeling/modelado.ipynb` is a single step instead of three.
- **Charts saved to disk, non-blocking.** `eda/`, `feature_engineering/` and `modeling/sarima_backup.py` use a non-interactive matplotlib backend (`Agg`) and save every chart to their own `img/` folder (`plt.savefig`), so running them as plain scripts doesn't pop up windows you have to close by hand, and results are still there to look at afterwards.
- **Only the imports each file actually uses.** The original notebook imported the full modeling stack (`statsmodels`, `pmdarima`, `prophet`, `sklearn`, `plotly`...) at the very top, before any of it was needed. Each split-out file now imports only what it uses.
- **SARIMA archived, Prophet is what's active.** The SARIMA/SARIMAX exploration and the SARIMA side of the SARIMA-vs-Prophet comparison moved out of `modeling/modelado.ipynb` into `modeling/sarima_backup.py`, unmodified; the notebook now only has the Prophet-based modeling and the anomaly-detection results.
- **A few bugs fixed along the way:** an undefined `{i}` in some ACF/PACF plot titles (`feature_engineering/feature_engineering.py`), Prophet's confidence-interval columns (`yhat_lower`/`yhat_upper`) never being saved before a cell that used them (`modeling/modelado.ipynb`), and the same expensive `groupby` being computed twice in a row for no reason (`modeling/modelado.ipynb`).
- **Full-series prediction plot + cross-validation for Prophet.** The single-station demo used to only plot Prophet's predictions over the test slice; it now also plots the full train+test fit/forecast, and adds a proper cross-validation section (`prophet.diagnostics.cross_validation` with rolling cutoffs, instead of relying on a single 85/15 split) to get a more robust read on error by forecast horizon.
- **`dashboard/` prototype added.** A first pass at a Streamlit map of the network (demand and anomalies per station) - see its own section above and `dashboard/ANALISIS.md`.

## Current state

- Data pipeline produces four checkpoints (`data/processed/*.pkl`) so each stage — including `modeling/` — can load processed data directly instead of re-running everything before it.
- Anomaly detection is centered on one model: `motor_auditoria_consenso_mad_bidireccional`, which fits Prophet per station/line and flags anomalies by combining Prophet's confidence interval with a robust (MAD-based) z-score, across all series at once. Prophet is not trained on station-closure days (afluencia=0) so those days don't bias the learned trend, but it still predicts on them so real closures keep getting flagged as anomalies. An earlier single-station Prophet prototype and a separate LightGBM experiment were both removed in favor of this single scaled model.
- A stratified sample of critical anomalies was manually investigated (OSINT) and logged in `bitacora_investigacion_anomalias_criticas.csv`, used to validate and analyze the detected anomalies.
- Next steps under consideration: adding more regressors to Prophet, and evaluating Isolation Forest as an alternative/complementary anomaly detector.