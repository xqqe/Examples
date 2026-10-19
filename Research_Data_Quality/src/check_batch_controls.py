from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
RESULTS_DIR = PROJECT_DIR / "results"


def complete_replicates(group):
    """Require exactly the three expected control replicates."""
    return (
        len(group) == 3
        and set(group["replicate"]) == {1, 2, 3}
    )


def valid_counts(values):
    return (
        values.notna()
        & np.isfinite(values)
        & values.ge(0)
        & values.mod(1).eq(0)
    )


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    samples = pd.read_csv(DATA_DIR / "samples.csv")
    controls = pd.read_csv(DATA_DIR / "batch_controls.csv")
    images = pd.read_csv(DATA_DIR / "images_with_qc.csv")

    # Iterate over expected batches so missing controls remain visible.
    results = []

    for batch_id in sorted(samples["batch_id"].dropna().unique()):
        batch = controls.loc[controls["batch_id"].eq(batch_id)]

        result = {"batch_id": batch_id}

        for control_type, prefix, lower, upper in [
            ("blank", "blank", 0, 60),
            ("fluorescence_reference", "fluorescence", 850, 1150),
        ]:
            group = batch.loc[batch["control_type"].eq(control_type)]
            values = group["mean_fluorescence_au"]

            valid_values = (
                values.notna()
                & np.isfinite(values)
                & values.ge(0)
            )

            evaluable = (
                complete_replicates(group)
                and bool(valid_values.all())
            )

            median = values.loc[valid_values].median()

            # Blank must be strictly below 60; reference limits are inclusive.
            within_limits = (
                lower <= median < upper
                if prefix == "blank"
                else lower <= median <= upper
            )

            result[f"{prefix}_replicates"] = len(group)
            result[f"{prefix}_median_au"] = median
            result[f"{prefix}_evaluable"] = evaluable
            result[f"{prefix}_pass"] = (
                evaluable and bool(within_limits)
            )

        group = batch.loc[
            batch["control_type"].eq("live_cell_reference")
        ]

        total = group["reference_cell_count"]
        live = group["live_cell_count"]

        valid = (
            valid_counts(total)
            & valid_counts(live)
            & total.gt(0)
            & live.le(total)
        )

        evaluable = (
            complete_replicates(group)
            and bool(valid.all())
        )

        # Median of replicate viability fractions, as specified in the protocol.
        median_viability = (
            live.loc[valid] / total.loc[valid]
        ).median()

        result["viability_replicates"] = len(group)
        result["viability_median_fraction"] = median_viability
        result["viability_evaluable"] = evaluable
        result["viability_pass"] = (
            evaluable and bool(median_viability >= 0.90)
        )

        results.append(result)

    batch_qc = pd.DataFrame(results)
    batch_qc.to_csv(RESULTS_DIR / "batch_qc.csv", index=False)

    combined = images.merge(
        batch_qc,
        on="batch_id",
        how="left",
        validate="many_to_one",
    )

    # Conservative primary-analysis policy:
    # fluorescence requires passing both optical controls.
    optical_controls_pass = (
        combined["blank_pass"].eq(True)
        & combined["fluorescence_pass"].eq(True)
    )

    combined["primary_eligible_fluorescence"] = (
        combined["image_eligible_fluorescence"]
        & optical_controls_pass
    )

    combined["primary_eligible_viability"] = (
        combined["image_eligible_viability"]
        & combined["viability_pass"].eq(True)
    )

    # These controls do not independently validate total cell counting.
    combined["primary_eligible_cell_count"] = (
        combined["image_eligible_cell_count"]
    )

    combined.to_csv(
        DATA_DIR / "images_with_batch_qc.csv",
        index=False,
    )

    print("\nBatch control results:")
    print(
        batch_qc[
            [
                "batch_id",
                "blank_median_au",
                "fluorescence_median_au",
                "viability_median_fraction",
                "blank_pass",
                "fluorescence_pass",
                "viability_pass",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
    