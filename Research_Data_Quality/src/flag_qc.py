from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
RESULTS_DIR = PROJECT_DIR / "results"


def valid_count(values):
    """A count must be present, finite, non-negative, and an integer."""
    return (
        values.notna()
        & np.isfinite(values)
        & values.ge(0)
        & values.mod(1).eq(0)
    )


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    samples = pd.read_csv(DATA_DIR / "samples.csv")
    images = pd.read_csv(DATA_DIR / "image_measurements.csv")

    # A left join preserves images even when their sample ID is unmatched.
    data = images.merge(
        samples,
        on="sample_id",
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    # Record individual problems rather than one unexplained pass/fail label.
    data["qc_unmatched_sample"] = data["_merge"].ne("both")

    data["qc_invalid_cell_count"] = ~valid_count(data["cell_count"])

    data["qc_invalid_live_count"] = (
        ~valid_count(data["live_cell_count"])
        | data["live_cell_count"].gt(data["cell_count"])
    )

    data["qc_invalid_fluorescence"] = ~(
        data["mean_fluorescence_au"].notna()
        & np.isfinite(data["mean_fluorescence_au"])
        & data["mean_fluorescence_au"].ge(0)
    )

    # Missing or out-of-range focus scores cannot pass focus QC.
    data["qc_failed_focus"] = ~data["focus_score"].between(0.70, 1.00)

    data["qc_invalid_field_index"] = ~data["field_index"].isin([1, 2, 3, 4])

    data["qc_repeated_sample_field"] = data.duplicated(
        subset=["sample_id", "field_index"],
        keep=False,
    )

    # Check the documented relationship between treatment and concentration.
    valid_condition = (
        (
            data["treatment"].eq("vehicle")
            & data["dose_uM"].eq(0)
        )
        | (
            data["treatment"].eq("Compound_A")
            & data["dose_uM"].isin([0.1, 1, 10])
        )
    )

    data["qc_unresolved_condition"] = ~valid_condition

    # These are IMAGE-LEVEL eligibility flags.
    # Batch controls will be assessed separately.
    image_ok = ~(
        data["qc_unmatched_sample"]
        | data["qc_failed_focus"]
        | data["qc_invalid_field_index"]
        | data["qc_repeated_sample_field"]
    )

    data["image_eligible_cell_count"] = (
        image_ok & ~data["qc_invalid_cell_count"]
    )

    data["image_eligible_viability"] = (
        data["image_eligible_cell_count"]
        & ~data["qc_invalid_live_count"]
        & data["cell_count"].gt(0)
    )

    data["image_eligible_fluorescence"] = (
        image_ok
        & ~data["qc_invalid_fluorescence"]
        & data["cell_count"].gt(0)
    )

    # Calculate viability only where its numerator and denominator are valid.
    data["viability_fraction"] = (
        data["live_cell_count"]
        .div(data["cell_count"].where(data["cell_count"].gt(0)))
        .where(data["image_eligible_viability"])
    )

    # Missing treatment metadata prevents dose-response analysis,
    # but does not itself prove that an image measurement is bad.
    data["eligible_dose_comparison"] = ~data["qc_unresolved_condition"]

    data = data.drop(columns="_merge")
    data.to_csv(DATA_DIR / "images_with_qc.csv", index=False)

    flag_columns = [
        column for column in data.columns
        if column.startswith("qc_")
    ]

    summary = (
        data[flag_columns]
        .sum()
        .rename("flagged_rows")
        .rename_axis("check")
    )

    summary.to_csv(RESULTS_DIR / "image_qc_summary.csv")

    flagged = data[flag_columns].any(axis=1)
    data.loc[flagged].to_csv(
        RESULTS_DIR / "flagged_images.csv",
        index=False,
    )

    print("\nQC summary:")
    print(summary.to_string())
    print("\nSaved images_with_qc.csv and QC reports.")


if __name__ == "__main__":
    main()