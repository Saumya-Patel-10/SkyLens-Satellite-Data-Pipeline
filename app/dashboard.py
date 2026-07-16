"""Stage 4 - Presentation (Streamlit dashboard).

In a 48-hour format the presentation carries almost as much weight as the code,
so this front-end is built to *tell the story in order*: headline -> trend ->
when -> where -> how we cleaned the data. Each section maps to one panel.

Run:  streamlit run app/dashboard.py
(Run the pipeline first: python -m src.pipeline)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Make `src` importable when Streamlit runs this file directly.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.config import load_config, resolve_path  # noqa: E402

st.set_page_config(page_title="SkyLens", page_icon="🛰️", layout="wide")


@st.cache_data
def load_outputs(processed_path: str):
    p = resolve_path(processed_path)
    data = {
        "timeseries": pd.read_parquet(p / "timeseries.parquet"),
        "seasonal": pd.read_parquet(p / "seasonal.parquet"),
        "spatial": pd.read_parquet(p / "spatial.parquet"),
        "hotspots": pd.read_parquet(p / "hotspots.parquet"),
    }
    with open(p / "summary.json", encoding="utf-8") as fh:
        data["summary"] = json.load(fh)
    return data


cfg = load_config()

st.title(f"🛰️ {cfg['project']['name']}")
st.caption(f"NASA Space Apps · {cfg['project']['challenge']}")
st.subheader(cfg["project"]["one_question"].strip())

try:
    d = load_outputs(cfg["data"]["processed_path"])
except FileNotFoundError:
    st.warning("No outputs found. Run the pipeline first:  "
               "`python -m src.pipeline`")
    st.stop()

units = cfg["data"]["units"]
trend = d["summary"]["trend"]
qc = d["summary"]["qc_report"]

# --- Headline numbers (the one-glance takeaway) ---------------------------
c1, c2, c3 = st.columns(3)
c1.metric("Trend", f"{trend['slope_per_year']:+.3f} {units}/yr",
          trend["direction"])
c2.metric("Trend fit (R²)", f"{trend['r2']:.2f}")
c3.metric("Data retained after QC", f"{qc['retained_pct']}%")

st.divider()

# --- WHEN: trend + seasonality -------------------------------------------
left, right = st.columns(2)
with left:
    st.markdown("**Regional average over time**")
    ts = d["timeseries"].set_index("time")["value"]
    st.line_chart(ts)
with right:
    st.markdown("**Seasonal profile (mean by month)**")
    seas = d["seasonal"].set_index("month")["value"]
    st.bar_chart(seas)

st.divider()

# --- WHERE: spatial map + hotspot ranking --------------------------------
st.markdown("**Where it's worst — time-averaged map**")
mleft, mright = st.columns([2, 1])
with mleft:
    grid = d["spatial"]
    # Rename to lat/lon so st.map can place points; size by value.
    st.map(grid.rename(columns={"lat": "lat", "lon": "lon"}),
           latitude="lat", longitude="lon", size="value")
with mright:
    st.markdown("Top hotspots")
    st.dataframe(d["hotspots"].round(2), hide_index=True,
                 use_container_width=True)

st.divider()

# --- HONESTY: the QC audit trail -----------------------------------------
with st.expander("How we cleaned the data (QC audit trail)"):
    st.write(
        f"Started with {qc['start_rows']:,} observations. "
        f"Dropped {qc['dropped_missing']:,} missing, "
        f"{qc['dropped_cloudy']:,} cloud-contaminated, "
        f"{qc['dropped_out_of_range']:,} out-of-range, and "
        f"{qc['dropped_outliers']:,} statistical outliers — "
        f"retaining {qc['retained_pct']}%."
    )
    st.json(qc)

st.caption("Data source: "
           f"`{cfg['data']['source']}` · Region: {cfg['region']['name']}")
