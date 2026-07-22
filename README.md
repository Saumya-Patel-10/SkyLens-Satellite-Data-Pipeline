# 🛰️ SkyLens — NASA Space Apps Challenge 2026 Starter

A ready-to-run **data pipeline + dashboard** scaffold for the NASA Space Apps
Challenge (event: **Nov 14–15, 2026**; challenge list drops ~mid-October). It
implements the four-stage structure the event rewards —
**ingest → clean → analyze → present** — and runs end-to-end *offline* on
synthetic data so your demo is green *before* the real dataset exists.

> The worked example is satellite **air-quality exploration**, chosen to lean on
> Python + data-pipeline + visualization skills (the "data exploration / data
> visualization" lane) rather than unfamiliar image-classification/ML. Swap in
> any gridded space-time dataset by editing **one config file** and **one
> loader function**.

## Why it's built this way
The brief's core lesson: **teams win by telling a clear story with the data, not
by stacking complex ML.** So the code is deliberately small and legible, and the
strategy lives in [`docs/STORY.md`](docs/STORY.md) — read that first.

## Quickstart
```bash
pip install -r requirements.txt   # or: make setup
python -m src.pipeline            # ingest -> clean -> analyze (writes to data/)
streamlit run app/dashboard.py    # open the dashboard
pytest -q                         # run the tests
```
No downloads or network needed — `data.source: synthetic` in the config
generates realistic messy data (missing retrievals, cloud contamination,
outliers) so the cleaning stage and dashboard have something real to chew on.

## Project structure
```
nasa-space-apps-2026/
├── README.md                 # you are here
├── requirements.txt          # deps (+ commented event-day extras)
├── Makefile                  # make setup | pipeline | app | test | clean
├── .gitignore
│
├── config/
│   └── config.yaml           # THE knob: region, dates, variable, QC thresholds
│
├── data/                     # pipeline artifacts (gitignored)
│   ├── raw/                  #   1. ingested data lands here
│   ├── interim/              #   2. cleaned data
│   └── processed/            #   3. analysis outputs the dashboard reads
│
├── src/                      # reusable pipeline logic
│   ├── config.py             #   config loader / path resolver
│   ├── ingest.py             #   STAGE 1  synthetic gen + csv/netcdf seams
│   ├── clean.py              #   STAGE 2  QC with an audit trail
│   ├── analyze.py            #   STAGE 3  trend / seasonality / hotspots
│   └── pipeline.py           #   orchestrates 1->2->3
│
├── app/
│   └── dashboard.py          # STAGE 4  Streamlit story: headline/when/where/QC
│
├── notebooks/
│   └── 01_exploration.md     # scratch exploration + event-day checklist
│
├── tests/
│   └── test_pipeline.py      # locks the data contract + QC guarantees
│
└── docs/
    └── STORY.md              # scoping + presentation strategy (read first)
```

## How the four stages map to the code
| Stage | What it does | File | Contract |
|------|---------------|------|----------|
| 1. Ingest | Any source → one tidy table | `src/ingest.py` | cols: `time, lat, lon, value, cloud_fraction` |
| 2. Clean | Drop missing/cloudy/impossible/outliers, log what & why | `src/clean.py` | returns clean df + QC report |
| 3. Analyze | Answer the one question (trend, season, hotspots) | `src/analyze.py` | returns plottable DataFrames |
| 4. Present | Story-ordered dashboard | `app/dashboard.py` | reads `data/processed/` |

Because every stage talks through that fixed **tidy-table contract**, swapping
data never ripples past `ingest.py`.

## Using real NASA (or partner) data on event day
1. Put the real files in `data/raw/`.
2. In `config/config.yaml` set `data.source` to `csv` or `netcdf`, and update
   `data.variable`, `data.units`, the `region` box, and `time` range.
3. Implement the matching loader body in `src/ingest.py`
   (`load_csv` / `load_netcdf`) so it returns the contract columns. Tip: NASA
   gridded products are often netCDF/HDF — `xarray.open_dataset(...)` →
   `.to_dataframe()` gets you most of the way.
4. Check the real **QC/cloud-flag** columns and point `src/clean.py` at them.
5. `python -m src.pipeline && streamlit run app/dashboard.py`.

Consider **Space Agency Partner** data (ESA, JAXA, …) too — sometimes a partner
product fits your question better than NASA's own, and swapping is cheap here.

## The 48-hour game plan
- **Hour 0:** copy the real question into `config.yaml`, fill the scoping
  checklist in `docs/STORY.md`, freeze your non-goals.
- **Hours 1–2:** explore the real data (see `notebooks/01_exploration.md`),
  then wire the loader.
- **Middle:** point cleaning at the real QC flags; sanity-check the analysis.
- **Last third:** polish the dashboard and rehearse the story. In a 48-hour
  format the presentation carries almost as much weight as the code.

## License / attribution
Add your dataset attributions here before submitting (NASA and any partner
agencies require credit).
