from __future__ import annotations

import argparse
from pathlib import Path

import json

from src.benchmarks.benchmark_runner import run_benchmark, run_sensitivity_sweep, run_suite
from src.benchmarks.benchmark_config import load_scenario_config
from src.simulation.scenario_runner import run_scenario
from src.visualization.queue_plots import plot_queue_delay
from src.visualization.solver_comparison import plot_solver_latency


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="QEdge6G CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run-scenario")
    run_parser.add_argument("--base", default="configs/base.yaml")
    run_parser.add_argument("--scenario", required=True)
    run_parser.add_argument("--solver", default="greedy")
    run_parser.add_argument("--steps", type=int)

    benchmark_parser = subparsers.add_parser("benchmark")
    benchmark_parser.add_argument("--base", default="configs/base.yaml")
    benchmark_parser.add_argument("--scenario", required=True)
    benchmark_parser.add_argument("--solvers", nargs="+", required=True)
    benchmark_parser.add_argument("--steps", type=int)
    benchmark_parser.add_argument("--output", required=True)

    suite_parser = subparsers.add_parser("benchmark-suite")
    suite_parser.add_argument("--base", default="configs/base.yaml")
    suite_parser.add_argument("--output-dir", default="results/tables")
    suite_parser.add_argument(
        "--scenarios",
        nargs="*",
        default=[
            "configs/simulation/wireless_dense.yaml",
            "configs/simulation/tcp_bursty.yaml",
            "configs/simulation/edge_overload.yaml",
            "configs/simulation/mobility_event.yaml",
            "configs/simulation/trace_replay.yaml",
            "configs/simulation/tenant_slicing.yaml",
        ],
    )
    suite_parser.add_argument(
        "--solvers",
        nargs="+",
        default=["greedy", "shortest_path", "load_balanced", "exact", "simulated_annealing", "quantum_inspired"],
    )

    sweep_parser = subparsers.add_parser("sensitivity-sweep")
    sweep_parser.add_argument("--base", default="configs/base.yaml")
    sweep_parser.add_argument("--scenario", required=True)
    sweep_parser.add_argument("--solvers", nargs="+", required=True)
    sweep_parser.add_argument("--steps", type=int)
    sweep_parser.add_argument("--output", required=True)
    sweep_parser.add_argument("--sweep-config", required=True, help="JSON file mapping dotted config keys to lists of values")

    plot_parser = subparsers.add_parser("plot")
    plot_parser.add_argument("--input", required=True)
    plot_parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "run-scenario":
        config = load_scenario_config(args.base, args.scenario)
        rows, summary = run_scenario(config, solver_name=args.solver, steps=args.steps)
        print({"rows": len(rows), "summary": summary})
        return
    if args.command == "benchmark":
        run_benchmark(args.base, args.scenario, args.solvers, args.output, steps=args.steps)
        print(f"wrote {args.output}")
        return
    if args.command == "benchmark-suite":
        outputs = run_suite(args.base, args.scenarios, args.solvers, args.output_dir)
        print({"outputs": outputs})
        return
    if args.command == "sensitivity-sweep":
        sweep_dimensions = json.loads(Path(args.sweep_config).read_text(encoding="utf-8"))
        run_sensitivity_sweep(args.base, args.scenario, args.solvers, args.output, sweep_dimensions, steps=args.steps)
        print(f"wrote {args.output}")
        return
    if args.command == "plot":
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        plot_solver_latency(args.input, str(output_dir / "solver_latency.png"))
        plot_queue_delay(args.input, str(output_dir / "queue_delay.png"))
        print(f"wrote plots to {output_dir}")


if __name__ == "__main__":
    main()
