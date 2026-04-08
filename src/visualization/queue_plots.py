from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.visualization.solver_comparison import PALETTE, _style


def plot_queue_delay(input_csv: str, output_path: str) -> None:
    _style()
    df = pd.read_csv(input_csv)
    summary = (
        df.groupby("solver_name", as_index=False)
        .agg(
            queue_delay_ms=("queue_delay_ms", "mean"),
            transport_utilization=("transport_utilization", "mean"),
            edge_utilization=("edge_utilization", "mean"),
        )
        .sort_values("queue_delay_ms")
    )

    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5), constrained_layout=True)
    sns.barplot(data=summary, x="solver_name", y="queue_delay_ms", hue="solver_name", palette=PALETTE, dodge=False, legend=False, ax=axes[0])
    sns.stripplot(data=df, x="solver_name", y="queue_delay_ms", color="#222222", alpha=0.55, size=4, jitter=0.14, ax=axes[0])
    axes[0].set_title("Queue Delay Across Decision Windows")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Queue delay (ms)")
    axes[0].tick_params(axis="x", rotation=25)

    util_df = summary.melt(
        id_vars="solver_name",
        value_vars=["transport_utilization", "edge_utilization"],
        var_name="resource",
        value_name="utilization",
    )
    sns.barplot(data=util_df, x="solver_name", y="utilization", hue="resource", palette=["#5b8e7d", "#c97c5d"], ax=axes[1])
    axes[1].set_title("Dominant Utilization Pressure")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Utilization")
    axes[1].tick_params(axis="x", rotation=25)
    axes[1].legend(title="", frameon=False)

    fig.suptitle("Queue and Resource Pressure", fontsize=20, fontweight="bold")
    fig.savefig(output_path, dpi=220, bbox_inches="tight")
    plt.close(fig)
