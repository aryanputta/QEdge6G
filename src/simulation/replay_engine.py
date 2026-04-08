from __future__ import annotations

import csv
from pathlib import Path


def replay_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

