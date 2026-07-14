"""Stage 1 - Ingest.

Any source becomes one tidy table with the fixed contract columns:
`time, lat, lon, value, cloud_fraction`. Every downstream stage (clean,
analyze, dashboard) only ever talks to that contract, so swapping data
sources never ripples past this file.

`make_synthetic` is the offline default (`data.source: synthetic` in
config.yaml) - it fabricates a realistic, deliberately messy grid (missing
retrievals, cloud contamination, outliers) so the rest of the pipeline and
the tests are green before real data exists. `load_csv` / `load_netcdf` are
the seams to wire up on event day.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import resolve_path

CONTRACT_COLS = ["time", "lat", "lon", "value", "cloud_fraction"]


def make_synthetic(cfg: dict, seed: int = 0) -> pd.DataFrame:
    """Fabricate a tidy (time, lat, lon, value, cloud_fraction) table.

    Built from the config's region box, time range, and QC thresholds so it
    stays realistic: a mild trend + seasonality + spatial hotspot, plus
    missing retrievals, cloud contamination, and a few outlier spikes for
    the cleaning stage to earn its keep on.
    """
    rng = np.random.default_rng(seed)
    region = cfg["region"]
    time_cfg = cfg["time"]
    qc = cfg["quality_control"]

    lats = np.arange(region["lat_min"], region["lat_max"] + 1e-9,
                      region["grid_resolution"])
    lons = np.arange(region["lon_min"], region["lon_max"] + 1e-9,
                      region["grid_resolution"])
    times = pd.date_range(time_cfg["start"], time_cfg["end"],
                           freq=time_cfg["freq"])

    grid = pd.MultiIndex.from_product([times, lats, lons],
                                       names=["time", "lat", "lon"])
    df = grid.to_frame(index=False)
    n = len(df)

    # A mild long-term trend plus a seasonal wobble plus one spatial hotspot,
    # so the trend/seasonality/hotspot panels all have something to show.
    t_days = (df["time"] - times[0]).dt.days.to_numpy(dtype=float)
    trend = 0.01 * t_days / 365.25
    season = 3.0 * np.sin(2 * np.pi * (df["time"].dt.month.to_numpy() / 12.0))
    lat_c = (region["lat_min"] + region["lat_max"]) / 2
    lon_c = (region["lon_min"] + region["lon_max"]) / 2
    dist = np.hypot(df["lat"].to_numpy() - lat_c, df["lon"].to_numpy() - lon_c)
    hotspot = 5.0 * np.exp(-dist)
    noise = rng.normal(0, 1.0, n)

    baseline = (qc["min_valid"] + qc["max_valid"]) / 2
    df["value"] = baseline + trend + season + hotspot + noise
    df["cloud_fraction"] = rng.beta(2, 5, n)

    # Inject realistic messiness for the cleaning stage to remove.
    missing_mask = rng.random(n) < 0.03
    df.loc[missing_mask, "value"] = np.nan

    outlier_mask = rng.random(n) < 0.01
    df.loc[outlier_mask, "value"] += rng.choice([-1, 1], outlier_mask.sum()) * \
        rng.uniform(20, 40, outlier_mask.sum())

    out_of_range_mask = rng.random(n) < 0.01
    df.loc[out_of_range_mask, "value"] = rng.choice(
        [qc["min_valid"] - 5, qc["max_valid"] + 5], out_of_range_mask.sum())

    return df[CONTRACT_COLS]


def load_csv(path: str) -> pd.DataFrame:
    """Load a real CSV export into the tidy contract.

    Expects a header containing (at least) `time, lat, lon, value,
    cloud_fraction`. Wire this up on event day once the real column names
    are known - rename/derive columns here so everything downstream is
    untouched.
    """
    df = pd.read_csv(path, parse_dates=["time"])
    missing = set(CONTRACT_COLS) - set(df.columns)
    if missing:
        raise ValueError(
            f"load_csv: input is missing contract columns {sorted(missing)}. "
            f"Rename/derive them here so the output matches {CONTRACT_COLS}."
        )
    return df[CONTRACT_COLS]


def load_netcdf(path: str) -> pd.DataFrame:
    """Load a real netCDF/HDF granule into the tidy contract.

    NASA gridded products are commonly netCDF/HDF; `xarray.open_dataset(...)
    .to_dataframe()` gets you most of the way there. Uncomment `xarray`
    (and `netcdf4`) in requirements.txt before wiring this up.
    """
    try:
        import xarray as xr
    except ImportError as exc:
        raise NotImplementedError(
            "load_netcdf needs xarray - uncomment it in requirements.txt, "
            "pip install, then implement the open_dataset/to_dataframe "
            f"conversion to the contract columns {CONTRACT_COLS}."
        ) from exc

    ds = xr.open_dataset(path)
    df = ds.to_dataframe().reset_index()
    missing = set(CONTRACT_COLS) - set(df.columns)
    if missing:
        raise ValueError(
            f"load_netcdf: dataset is missing contract columns {sorted(missing)}. "
            f"Rename/derive them here so the output matches {CONTRACT_COLS}."
        )
    return df[CONTRACT_COLS]


def ingest(cfg: dict) -> pd.DataFrame:
    """Dispatch on `data.source` and return the tidy contract table.

    Also persists the raw table to `data/raw/` so the ingest step leaves
    an audit trail, same as clean and analyze do for their stages.
    """
    source = cfg["data"]["source"]
    if source == "synthetic":
        df = make_synthetic(cfg)
    elif source == "csv":
        df = load_csv(cfg["data"]["raw_path"])
    elif source == "netcdf":
        df = load_netcdf(cfg["data"]["raw_path"])
    else:
        raise ValueError(
            f"Unknown data.source '{source}' - expected 'synthetic', 'csv', "
            "or 'netcdf'."
        )

    out = resolve_path(cfg["data"]["raw_path"]) / "raw.parquet"
    df.reset_index(drop=True).to_parquet(out, index=False)
    print(f"[ingest] {source}: {len(df):,} rows -> {out}")
    return df.reset_index(drop=True)


if __name__ == "__main__":
    from .config import load_config

    cfg = load_config()
    raw = ingest(cfg)
    print(raw.describe())
