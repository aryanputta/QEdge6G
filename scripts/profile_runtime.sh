#!/usr/bin/env bash
set -euo pipefail

/usr/bin/time -l python3 -m src.cli benchmark --scenario "${1:-configs/simulation/wireless_dense.yaml}" --solvers greedy exact simulated_annealing quantum_inspired --output "${2:-results/tables/profile_run.csv}"

