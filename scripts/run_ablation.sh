#!/usr/bin/env bash
set -euo pipefail

python3 -m src.cli benchmark --scenario configs/simulation/mixed_workload_classes.yaml --solvers greedy exact simulated_annealing quantum_inspired --output "${1:-results/tables/ablation_mixed_workloads.csv}"

