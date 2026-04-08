PYTHON ?= python3

.PHONY: test smoke benchmark sweep plots lint

test:
	$(PYTHON) -m pytest

smoke:
	$(PYTHON) -m src.cli benchmark --scenario configs/simulation/wireless_dense.yaml --solvers greedy exact simulated_annealing quantum_inspired --steps 6 --output results/tables/smoke_wireless_dense.csv

benchmark:
	$(PYTHON) -m src.cli benchmark-suite --output-dir results/tables

sweep:
	$(PYTHON) -m src.cli sensitivity-sweep --scenario configs/simulation/wireless_dense.yaml --solvers greedy exact quantum_inspired --steps 3 --sweep-config configs/benchmark_sensitivity.json --output results/tables/sensitivity_sweep.csv

plots:
	$(PYTHON) -m src.cli plot --input results/tables/smoke_wireless_dense.csv --output-dir results/figures

lint:
	$(PYTHON) -m compileall src
