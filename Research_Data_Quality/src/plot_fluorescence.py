from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
RESULTS_DIR = PROJECT_DIR / "results"


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(DATA_DIR / "images_with_batch_qc.csv")

    # Include image-level usable measurements, including failed batches.
    # That lets us see batch problems rather than hiding them.
    plot_data = data.loc[
        data["image_eligible_fluorescence"]
        & data["eligible_dose_comparison"]
    ].copy()

    if plot_data.empty:
        raise ValueError("No eligible fluorescence measurements to plot.")

    # Treat dose as discrete groups, including the zero-dose control.
    doses = [0, 0.1, 1, 10]
    dose_positions = {dose: position for position, dose in enumerate(doses)}

    rng = np.random.default_rng(42)

    plot_data["plot_x"] = (
        plot_data["dose_uM"].map(dose_positions)
        + rng.uniform(-0.18, 0.18, len(plot_data))
    )

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    batches = sorted(plot_data["batch_id"].unique())
    colors = plt.get_cmap("tab10")

    for index, batch_id in enumerate(batches):
        group = plot_data.loc[plot_data["batch_id"].eq(batch_id)]

        # Batch status is constant within a batch.
        passed = (
            group["blank_pass"].all()
            and group["fluorescence_pass"].all()
        )

        label = batch_id if passed else f"{batch_id} — control failure"

        for ax in axes:
            ax.scatter(
                group["plot_x"],
                group["mean_fluorescence_au"],
                color=colors(index),
                marker="o" if passed else "x",
                alpha=0.55,
                s=20,
                label=label,
            )

    axes[0].set_title("Fluorescence — linear scale")
    axes[1].set_title("Fluorescence — logarithmic scale")

    # Zero is valid fluorescence but cannot appear on a log scale.
    zero_count = plot_data["mean_fluorescence_au"].eq(0).sum()
    axes[1].set_yscale("log")

    for ax in axes:
        ax.set_xticks(range(len(doses)))
        ax.set_xticklabels(["Vehicle", "0.1", "1", "10"])
        ax.set_xlabel("Compound A dose (µM)")
        ax.set_ylabel("Mean cellular fluorescence (AU)")
        ax.grid(axis="y", alpha=0.2)

    axes[1].legend(title="Batch", fontsize=8)
    fig.suptitle("Exploratory QC: each point is one image field")
    fig.tight_layout()

    fig.savefig(
        RESULTS_DIR / "fluorescence_qc.png",
        dpi=200,
        bbox_inches="tight",
    )

    largest = plot_data.nlargest(10, "mean_fluorescence_au")

    columns = [
        "image_id",
        "sample_id",
        "batch_id",
        "dose_uM",
        "mean_fluorescence_au",
        "focus_score",
    ]

    largest[columns].to_csv(
        RESULTS_DIR / "largest_fluorescence_values.csv",
        index=False,
    )

    print("\nTen largest fluorescence measurements:")
    print(largest[columns].to_string(index=False))
    print(f"\nZero values omitted from log-scale display: {zero_count}")

    plt.show()


if __name__ == "__main__":
    main()
    