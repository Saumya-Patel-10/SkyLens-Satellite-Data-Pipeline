"""Tests for the pipeline contract.

The point of testing a hackathon pipeline is NOT coverage vanity — it's that
you can refactor fast at 2am without breaking the demo. These lock down the
data contract and the QC guarantees.

Run:  pytest -q
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.analyze import linear_trend, regional_timeseries, run_analysis
from src.clean import clean
from src.config import load_config
from src.ingest import make_synthetic

CONTRACT_COLS = {"time", "lat", "lon", "value", "cloud_fraction"}


def _cfg():
    cfg = load_config()
    # Shrink for fast tests.
    cfg["time"]["start"] = "2022-01-01"
    cfg["time"]["end"] = "2022-06-01"
    return cfg


def test_ingest_matches_contract():
    df = make_synthetic(_cfg())
    assert CONTRACT_COLS.issubset(df.columns)
    assert len(df) > 0
    assert df["cloud_fraction"].between(0, 1).all()


def test_clean_removes_bad_data():
    cfg = _cfg()
    raw = make_synthetic(cfg)
    clean_df, report = clean(raw, cfg)

    # No missing values survive.
    assert clean_df["value"].notna().all()
    # Nothing above the physical ceiling survives.
    assert (clean_df["value"] <= cfg["quality_control"]["max_valid"]).all()
    # No overly-cloudy pixels survive.
    assert (clean_df["cloud_fraction"]
            <= cfg["quality_control"]["max_cloud_fraction"]).all()
    # The audit trail adds up.
    dropped = (report["dropped_missing"] + report["dropped_cloudy"]
               + report["dropped_out_of_range"] + report["dropped_outliers"])
    assert report["start_rows"] - dropped == report["end_rows"]


def test_trend_recovers_known_slope():
    # A perfectly linear series should recover its slope with R^2 == 1.
    times = pd.date_range("2020-01-01", periods=24, freq="MS")
    t_days = times.values.astype("datetime64[D]").astype(float)
    true_per_day = -0.01
    y = 10 + true_per_day * (t_days - t_days[0])
    ts = pd.DataFrame({"time": times, "value": y})
    out = linear_trend(ts)
    assert out["direction"] == "declining"
    assert out["r2"] > 0.99
    assert np.isclose(out["slope_per_year"], true_per_day * 365.25, atol=1e-3)


def test_full_pipeline_runs():
    cfg = _cfg()
    raw = make_synthetic(cfg)
    clean_df, _ = clean(raw, cfg)
    results = run_analysis(clean_df, cfg)
    assert set(results) == {"timeseries", "trend", "seasonal", "spatial",
                            "hotspots"}
    assert len(regional_timeseries(clean_df)) > 0
    assert len(results["hotspots"]) <= 5
