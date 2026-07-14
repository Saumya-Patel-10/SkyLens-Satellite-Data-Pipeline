"""Stage 2 - Cleaning & quality control.

Real scientific data is messy: missing retrievals, cloud contamination,
physically impossible values, sensor spikes. This stage turns the raw tidy
table into a trustworthy one and, crucially, *records what it removed* so you
can defend your numbers to judges.

Every rule is driven by config so reviewers can see your assumptions.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import load_config, resolve_path


def clean(df: pd.DataFrame, cfg: dict | None = None
          ) -> tuple[pd.DataFrame, dict]:
    """Apply QC rules and return (clean_df, report).

    The report dict is a small audit trail: counts dropped at each step. Put it
    on a slide - "we dropped X% cloud-contaminated pixels" is exactly the kind
    of honesty judges reward.
    """
    cfg = cfg or load_config()
    qc = cfg["quality_control"]
    report: dict[str, int] = {"start_rows": len(df)}

    df = df.copy()

    # 1. Drop rows with no retrieval at all.
    before = len(df)
    df = df.dropna(subset=["value"])
    report["dropped_missing"] = before - len(df)

    # 2. Drop cloud-contaminated observations.
    before = len(df)
    df = df[df["cloud_fraction"] <= qc["max_cloud_fraction"]]
    report["dropped_cloudy"] = before - len(df)

    # 3. Drop physically implausible values (below floor / above ceiling).
    before = len(df)
    df = df[(df["value"] >= qc["min_valid"]) & (df["value"] <= qc["max_valid"])]
    report["dropped_out_of_range"] = before - len(df)

    # 4. Flag statistical outliers per-timestep (robust z via MAD) and drop.
    before = len(df)
    df = _drop_outliers(df, z=qc["outlier_z"])
    report["dropped_outliers"] = before - len(df)

    report["end_rows"] = len(df)
    report["retained_pct"] = round(100 * len(df) / report["start_rows"], 1)

    out = resolve_path(cfg["data"]["interim_path"]) / "clean.parquet"
    df.reset_index(drop=True).to_parquet(out, index=False)
    print(f"[clean] retained {report['end_rows']:,}/{report['start_rows']:,} "
          f"rows ({report['retained_pct']}%) -> {out}")
    return df.reset_index(drop=True), report


def _drop_outliers(df: pd.DataFrame, z: float) -> pd.DataFrame:
    """Robust outlier removal within each timestep using the modified z-score
    (based on the median absolute deviation, so a few spikes don't hide
    behind an inflated standard deviation).

    Implemented with groupby-transform rather than apply so all columns are
    preserved and it stays vectorised (fast, and immune to the pandas 3.x
    apply-drops-grouping-column behaviour)."""
    grp = df.groupby("time")["value"]
    median = grp.transform("median")
    abs_dev = (df["value"] - median).abs()
    # MAD per timestep = median of the absolute deviations within that step.
    mad = abs_dev.groupby(df["time"]).transform("median")

    mod_z = pd.Series(0.0, index=df.index)
    nonzero = mad != 0
    mod_z[nonzero] = 0.6745 * abs_dev[nonzero] / mad[nonzero]
    return df[mod_z <= z]


if __name__ == "__main__":
    from .ingest import ingest

    cfg = load_config()
    raw = ingest(cfg)
    _, rep = clean(raw, cfg)
    print(rep)
