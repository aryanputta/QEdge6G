#!/usr/bin/env bash
set -euo pipefail

python3 -m src.cli benchmark-suite --output-dir "${1:-results/tables}"

