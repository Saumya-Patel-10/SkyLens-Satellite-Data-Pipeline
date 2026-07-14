"""Stage 3 - Analysis.

This is where the *one question* gets answered. The whole design bet (see
docs/STORY.md) is: a narrow, well-explained insight beats a broad shallow one.
So the analysis is deliberately small and legible:

  1. Regional time series + a linear trend  -> "is it getting better/worse?"
  2. Seasonal profile (month-of-year means) -> "when is it worst?"
  3. Spatial mean map + hotspot ranking      -> "where is it worst?"

Each function returns a plain DataFrame the dashboard can plot directly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import load_config, resolve_path


def regional_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    """Spatial mean per timestep -> a single line the story hangs on."""
    ts = (df.groupby("time")["value"]
            .mean()
            .rename("value")
            .reset_index()
            .sort_values("time"))
    return ts


def linear_trend(ts: pd.DataFrame) -> dict:
    """Fit value ~ time (ordinary least squares) and report slope per year."""
    t = ts["time"].values.astype("datetime64[D]").astype(float)  # days
    y = ts["value"].values
    slope_per_day, intercept = np.polyfit(t, y, 1)
    slope_per_year = slope_per_day * 365.25
    # Simple R^2 for credibility on the slide.
    pred = slope_per_day * t + intercept
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")
    return {
        "slope_per_year": round(float(slope_per_year), 4),
        "direction": "declining" if slope_per_year < 0 else "rising",
        "r2": round(r2, 3),
    }


def seasonal_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Mean by calendar month -> the seasonality panel."""
    prof = (df.assign(month=df["time"].dt.month)
              .groupby("month")["value"]
              .mean()
              .reindex(range(1, 13))
              .rename("value")
              .reset_index())
    return prof


def spatial_mean(df: pd.DataFrame) -> pd.DataFrame:
    """Time-averaged value per grid cell -> the map layer."""
    grid = (df.groupby(["lat", "lon"])["value"]
              .mean()
              .rename("value")
              .reset_index())
    return grid


def hotspots(df: pd.DataFrame, top_n: int = 5) -> pd.DataFrame:
    """Rank the worst grid cells -> the 'where' headline number."""
    grid = spatial_mean(df).sort_values("value", ascending=False)
    return grid.head(top_n).reset_index(drop=True)


def run_analysis(df: pd.DataFrame, cfg: dict | None = None) -> dict:
    """Compute everything the dashboard/story needs and persist it."""
    cfg = cfg or load_config()
    ts = regional_timeseries(df)
    results = {
        "timeseries": ts,
        "trend": linear_trend(ts),
        "seasonal": seasonal_profile(df),
        "spatial": spatial_mean(df),
        "hotspots": hotspots(df),
    }

    out_dir = resolve_path(cfg["data"]["processed_path"])
    ts.to_parquet(out_dir / "timeseries.parquet", index=False)
    results["seasonal"].to_parquet(out_dir / "seasonal.parquet", index=False)
    results["spatial"].to_parquet(out_dir / "spatial.parquet", index=False)
    results["hotspots"].to_parquet(out_dir / "hotspots.parquet", index=False)

    tr = results["trend"]
    print(f"[analyze] trend: {tr['direction']} "
          f"{tr['slope_per_year']} {cfg['data']['units']}/yr (R^2={tr['r2']})")
    return results


if __name__ == "__main__":
    from .clean import clean
    from .ingest import ingest

    cfg = load_config()
    raw = ingest(cfg)
    clean_df, _ = clean(raw, cfg)
    run_analysis(clean_df, cfg)
