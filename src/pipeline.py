"""End-to-end pipeline: ingest -> clean -> analyze.

Run the whole thing with:  python -m src.pipeline
This is what you run once to (re)generate everything the dashboard reads.
"""

from __future__ import annotations

import json

from .analyze import run_analysis
from .clean import clean
from .config import load_config, resolve_path
from .ingest import ingest


def run() -> dict:
    cfg = load_config()
    print(f"=== {cfg['project']['name']} pipeline ===")
    print(f"Question: {cfg['project']['one_question'].strip()}\n")

    raw = ingest(cfg)
    clean_df, report = clean(raw, cfg)
    results = run_analysis(clean_df, cfg)

    # Persist the QC audit trail + headline numbers for the dashboard/slides.
    summary = {
        "qc_report": report,
        "trend": results["trend"],
        "hotspots": results["hotspots"].to_dict(orient="records"),
    }
    out = resolve_path(cfg["data"]["processed_path"]) / "summary.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2)
    print(f"\n[pipeline] summary -> {out}")
    print("Done. Launch the dashboard with:  streamlit run app/dashboard.py")
    return summary


if __name__ == "__main__":
    run()
