# 01 — Exploration

This folder is for throwaway exploration you do *before and during* the event —
the messy sketching that never belongs in `src/`. Keep the reusable logic in
`src/`; keep the "what does this data even look like" work here.

A fast way to explore without a full Jupyter setup is to run the pipeline
modules directly and poke at the parquet outputs:

```python
import pandas as pd
from src.ingest import ingest
from src.clean import clean
from src.config import load_config

cfg = load_config()
raw = ingest(cfg)
raw.describe()                      # distributions, ranges, NaN counts
raw.groupby("time")["value"].mean() # quick temporal signal check

clean_df, report = clean(raw, cfg)
report                              # how much did QC remove, and why?
```

Suggested first-hour checklist on event day:
1. Open the real granule/CSV and print its columns, dtypes, and units.
2. Plot one timestep as a map — is north up? are lon values -180..180 or 0..360?
3. Find the QC/cloud flag columns — those drive `src/clean.py`.
4. Confirm the variable's real units and update `config.yaml`.
5. Only then wire `load_csv` / `load_netcdf` in `src/ingest.py`.
