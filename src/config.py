"""Load and expose project configuration.

Keeping config access in one place means the rest of the code never hard-codes
a region or a file path. On event day you touch config/config.yaml, not the
pipeline.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Project root = one level above this file's package directory.
ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "config.yaml"


def load_config(path: str | Path = CONFIG_PATH) -> dict[str, Any]:
    """Read the YAML config into a plain dict."""
    with open(path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    return cfg


def resolve_path(relative: str) -> Path:
    """Turn a config-relative path (e.g. 'data/raw/') into an absolute Path."""
    return ROOT / relative


if __name__ == "__main__":
    import json

    print(json.dumps(load_config(), indent=2, default=str))
