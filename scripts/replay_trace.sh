#!/usr/bin/env bash
set -euo pipefail

INPUT="${1:-results/tables/wireless_dense.csv}"

INPUT="$INPUT" python3 - <<'PY'
from src.simulation.replay_engine import replay_rows
import os
rows = replay_rows(os.environ["INPUT"])
print({"rows": len(rows), "first_row": rows[0] if rows else None})
PY
