#!/usr/bin/env bash
set -euo pipefail

python3 -m src.cli sensitivity-sweep \
  --scenario "${1:-configs/simulation/wireless_dense.yaml}" \
  --solvers greedy exact quantum_inspired \
  --steps 3 \
  --sweep-config "${2:-configs/benchmark_sensitivity_smoke.json}" \
  --output "${3:-results/tables/sensitivity_sweep.csv}"
