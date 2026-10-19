from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"


def summarize_sample(group):
    counts = group.loc[group["primary_eligible_cell_count"]]
    viability = group.loc[group["primary_eligible_viability"]]

    # Weighting fluorescence requires a valid positive cell count.
    fluorescence = group.loc[
        group["primary_eligible_fluorescence"]
        & group["image_eligible_cell_count"]
        & group["cell_count"].gt(0)
    ]

    total_cells = viability["cell_count"].sum()

    weighted_fluorescence = float("nan")
    if not fluorescence.empty:
        weighted_fluorescence = (
            fluorescence["mean_fluorescence_au"]
            .mul(fluorescence["cell_count"])
            .sum()
            / fluorescence["cell_count"].sum()
        )

    return {
        "sample_id": group["sample_id"].iloc[0],
        "n_fields_available": len(group),
        "n_fields_cell_count": len(counts),
        "n_fields_viability": len(viability),
        "n_fields_fluorescence": len(fluorescence),
        "mean_cells_per_field": counts["cell_count"].mean(),
        "viability_fraction": (
            viability["live_cell_count"].sum() / total_cells
            if total_cells > 0
            else float("nan")
        ),
        "mean_fluorescence_au": weighted_fluorescence,
    }


def main():
    samples = pd.read_csv(DATA_DIR / "samples.csv")
    images = pd.read_csv(DATA_DIR / "images_with_batch_qc.csv")

    # Unmatched image records remain in the QC file but cannot be
    # assigned to a known treatment well.
    matched = images.loc[
        ~images["qc_unmatched_sample"]
    ]

    summaries = pd.DataFrame([
        summarize_sample(group)
        for _, group in matched.groupby("sample_id")
    ])

    # Start from the sample inventory to retain wells with no usable images.
    wells = samples.merge(
        summaries,
        on="sample_id",
        how="left",
        validate="one_to_one",
    )

    coverage_columns = [
        "n_fields_available",
        "n_fields_cell_count",
        "n_fields_viability",
        "n_fields_fluorescence",
    ]

    wells[coverage_columns] = (
        wells[coverage_columns].fillna(0).astype(int)
    )

    # Keep the unresolved sample condition visible.
    wells["condition_resolved"] = (
        (
            wells["treatment"].eq("vehicle")
            & wells["dose_uM"].eq(0)
        )
        | (
            wells["treatment"].eq("Compound_A")
            & wells["dose_uM"].isin([0.1, 1, 10])
        )
    )

    wells.to_csv(DATA_DIR / "well_summary.csv", index=False)

    print("\nFirst five well summaries:")
    print(wells.head().to_string(index=False))

    print("\nUsable image fields per endpoint:")
    print(wells[coverage_columns].sum().to_string())

    print("\nWells with unresolved treatment conditions:")
    print(
        wells.loc[
            ~wells["condition_resolved"],
            ["sample_id", "treatment", "dose_uM"],
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()