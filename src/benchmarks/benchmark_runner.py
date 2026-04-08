from __future__ import annotations

import csv
import itertools
from copy import deepcopy
from pathlib import Path

from src.benchmarks.benchmark_config import load_scenario_config
from src.simulation.scenario_runner import run_scenario


def run_benchmark(base_config: str, scenario_config: str, solvers: list[str], output_path: str, steps: int | None = None) -> list[dict]:
    config = load_scenario_config(base_config, scenario_config)
    rows: list[dict] = []
    for solver in solvers:
        solver_rows, _ = run_scenario(config, solver_name=solver, steps=steps)
        rows.extend(solver_rows)
    write_rows(rows, output_path)
    return rows


def run_suite(base_config: str, scenario_paths: list[str], solvers: list[str], output_dir: str) -> list[str]:
    output_paths: list[str] = []
    for scenario_path in scenario_paths:
        scenario_name = Path(scenario_path).stem
        output_path = str(Path(output_dir) / f"{scenario_name}.csv")
        run_benchmark(base_config, scenario_path, solvers, output_path)
        output_paths.append(output_path)
    return output_paths


def run_sensitivity_sweep(
    base_config: str,
    scenario_config: str,
    solvers: list[str],
    output_path: str,
    sweep_dimensions: dict[str, list],
    steps: int | None = None,
) -> list[dict]:
    base = load_scenario_config(base_config, scenario_config)
    rows: list[dict] = []
    sweep_keys = list(sweep_dimensions)
    sweep_values = [sweep_dimensions[key] for key in sweep_keys]
    for combination in itertools.product(*sweep_values):
        config = deepcopy(base)
        label_parts = []
        for key, value in zip(sweep_keys, combination):
            set_nested_value(config, key, value)
            label_parts.append(f"{key}={value}")
        sweep_label = "|".join(label_parts)
        for solver in solvers:
            solver_rows, _ = run_scenario(config, solver_name=solver, steps=steps)
            for row in solver_rows:
                for key, value in zip(sweep_keys, combination):
                    row[key] = value
                row["sweep_label"] = sweep_label
                rows.append(row)
    write_rows(rows, output_path)
    return rows


def write_rows(rows: list[dict], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def set_nested_value(config: dict, dotted_key: str, value) -> None:
    parts = dotted_key.split(".")
    current = config
    for part in parts[:-1]:
        current = current.setdefault(part, {})
    current[parts[-1]] = value
