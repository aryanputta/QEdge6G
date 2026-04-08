from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


PALETTE = {
    "greedy": "#355070",
    "shortest_path_nearest_edge": "#6d597a",
    "load_balanced": "#2a9d8f",
    "milp_exact": "#bc6c25",
    "exact_small_scale": "#bc6c25",
    "simulated_annealing": "#e76f51",
    "quantum_inspired": "#264653",
}


def _style() -> None:
    sns.set_theme(
        style="whitegrid",
        context="talk",
        rc={
            "axes.facecolor": "#f5f3ef",
            "figure.facecolor": "#fbfaf8",
            "grid.color": "#d8d2c8",
            "axes.edgecolor": "#b9b1a5",
            "axes.titleweight": "bold",
            "font.family": "DejaVu Sans",
        },
    )


def plot_solver_latency(input_csv: str, output_path: str) -> None:
    _style()
    df = pd.read_csv(input_csv)
    summary = (
        df.groupby("solver_name", as_index=False)
        .agg(
            p95_latency_ms=("p95_latency_ms", "mean"),
            goodput_mbps=("goodput_mbps", "mean"),
            fairness_index=("fairness_index", "mean"),
            solver_runtime_s=("solver_runtime_s", "mean"),
        )
        .sort_values("p95_latency_ms")
    )

    fig, axes = plt.subplots(2, 2, figsize=(16, 11), constrained_layout=True)

    sns.barplot(
        data=summary,
        x="solver_name",
        y="p95_latency_ms",
        hue="solver_name",
        palette=PALETTE,
        dodge=False,
        legend=False,
        ax=axes[0, 0],
    )
    sns.stripplot(
        data=df,
        x="solver_name",
        y="p95_latency_ms",
        color="#1d1d1d",
        size=4,
        jitter=0.15,
        alpha=0.55,
        ax=axes[0, 0],
    )
    axes[0, 0].set_title("Tail Latency by Solver")
    axes[0, 0].set_xlabel("")
    axes[0, 0].set_ylabel("p95 latency (ms)")
    axes[0, 0].tick_params(axis="x", rotation=25)

    sns.scatterplot(
        data=summary,
        x="goodput_mbps",
        y="fairness_index",
        hue="solver_name",
        palette=PALETTE,
        s=170,
        legend=False,
        ax=axes[0, 1],
    )
    for _, row in summary.iterrows():
        axes[0, 1].annotate(row["solver_name"], (row["goodput_mbps"], row["fairness_index"]), xytext=(6, 6), textcoords="offset points", fontsize=10)
    axes[0, 1].set_title("Goodput vs Fairness")
    axes[0, 1].set_xlabel("Goodput (Mbps)")
    axes[0, 1].set_ylabel("Fairness index")

    runtime_sorted = summary.sort_values("solver_runtime_s")
    sns.barplot(
        data=runtime_sorted,
        x="solver_name",
        y="solver_runtime_s",
        hue="solver_name",
        palette=PALETTE,
        dodge=False,
        legend=False,
        ax=axes[1, 0],
    )
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_title("Runtime per Decision Window")
    axes[1, 0].set_xlabel("")
    axes[1, 0].set_ylabel("Runtime (s, log scale)")
    axes[1, 0].tick_params(axis="x", rotation=25)

    ordered_solvers = list(summary["solver_name"])
    sns.lineplot(
        data=df,
        x="time_slot",
        y="p95_latency_ms",
        hue="solver_name",
        hue_order=ordered_solvers,
        palette=PALETTE,
        marker="o",
        linewidth=2.2,
        ax=axes[1, 1],
    )
    axes[1, 1].set_title("Step-Level Tail Latency Trajectory")
    axes[1, 1].set_xlabel("Time slot")
    axes[1, 1].set_ylabel("p95 latency (ms)")
    axes[1, 1].legend(title="", frameon=False, ncol=2)

    fig.suptitle("QEdge6G Solver Benchmark Report", fontsize=22, fontweight="bold")
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
