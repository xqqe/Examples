from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
RESULTS_DIR = PROJECT_DIR / "results"


def report(name, rows):
    """Display flagged rows and save them for review."""
    print(f"\n{name}: {len(rows)} flagged rows")

    if not rows.empty:
        print(rows.head(10).to_string(index=False))

    rows.to_csv(RESULTS_DIR / f"{name}.csv", index=False)


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    samples = pd.read_csv(DATA_DIR / "samples.csv")
    images = pd.read_csv(DATA_DIR / "image_measurements.csv")
    controls = pd.read_csv(DATA_DIR / "batch_controls.csv")

    # Flag every occurrence of a repeated ID, including the first.
    for name, table, id_column in [
        ("samples", samples, "sample_id"),
        ("images", images, "image_id"),
        ("controls", controls, "control_id"),
    ]:
        report(
            f"{name}_duplicate_ids",
            table.loc[table[id_column].duplicated(keep=False)],
        )

        report(
            f"{name}_missing_values",
            table.loc[table.isna().any(axis=1)],
        )

    # Compare image references against sample IDs exactly as exported.
    # Formatting differences may explain some unmatched references.
    report(
        "images_unmatched_sample_ids",
        images.loc[~images["sample_id"].isin(samples["sample_id"])],
    )

    report(
        "controls_unmatched_batch_ids",
        controls.loc[~controls["batch_id"].isin(samples["batch_id"])],
    )

    # Check counts for impossible values or non-integer measurements.
    counts = images[["cell_count", "live_cell_count"]]

    invalid_counts = (
        counts.lt(0).any(axis=1)
        | (counts.notna() & counts.mod(1).ne(0)).any(axis=1)
        | images["live_cell_count"].gt(images["cell_count"])
    )

    report("images_invalid_counts", images.loc[invalid_counts])

    report(
        "images_negative_fluorescence",
        images.loc[images["mean_fluorescence_au"] < 0],
    )

    report(
        "images_invalid_focus_score",
        images.loc[
            (images["focus_score"] < 0)
            | (images["focus_score"] > 1)
        ],
    )

    report(
        "images_failed_focus",
        images.loc[images["focus_score"] < 0.70],
    )

    # repr() exposes spaces that ordinary printing can conceal.
    print("\nTreatment labels exactly as recorded:")
    for label in samples["treatment"].unique():
        print(repr(label))

    print(f"\nAudit reports saved to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()