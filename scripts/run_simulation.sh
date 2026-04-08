#!/usr/bin/env bash
set -euo pipefail

python3 -m src.cli run-scenario --scenario "${1:-configs/simulation/wireless_dense.yaml}" --solver "${2:-greedy}"

