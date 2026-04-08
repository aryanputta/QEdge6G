from __future__ import annotations

from pathlib import Path

from src.utils.config_loader import load_config
from src.utils.validation import validate_config


def load_scenario_config(base_path: str | Path, scenario_path: str | Path) -> dict:
    config = load_config(base_path, scenario_path)
    validate_config(config)
    return config

