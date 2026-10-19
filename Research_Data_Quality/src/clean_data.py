from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_DIR / "data" / "raw"
CLEAN_DIR = PROJECT_DIR / "data" / "processed"
RESULTS_DIR = PROJECT_DIR / "results"


def main():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    samples = pd.read_csv(RAW_DIR / "samples.csv")
    images = pd.read_csv(RAW_DIR / "image_measurements.csv")
    controls = pd.read_csv(RAW_DIR / "batch_controls.csv")

    changes = []

    def normalize(table, table_name, column, transform):
        """Normalize a text column and record every changed value."""
        original = table[column].astype("string")
        updated = transform(original)

        changed = original.ne(updated).fillna(False)

        for index in table.index[changed]:
            changes.append({
                "table": table_name,
                "csv_row": index + 2,  # Header is row 1.
                "column": column,
                "original": original.loc[index],
                "updated": updated.loc[index],
            })

        table[column] = updated

    # IDs are defined as uppercase, without surrounding whitespace.
    for name, table, columns in [
        ("samples", samples,
         ["sample_id", "batch_id", "culture_id", "plate_id", "well"]),
        ("images", images, ["image_id", "sample_id"]),
        ("controls", controls, ["control_id", "batch_id"]),
    ]:
        for column in columns:
            normalize(
                table, name, column,
                lambda values: values.str.strip().str.upper(),
            )

    # Map known spelling variants to the documented treatment names.
    treatment_names = {
        "vehicle": "vehicle",
        "compound_a": "Compound_A",
        "compound a": "Compound_A",
    }

    def normalize_treatment(values):
        lookup = values.str.strip().str.lower()
        mapped = lookup.map(treatment_names)

        # Preserve unexpected labels so they remain visible for review.
        return mapped.fillna(values)

    normalize(samples, "samples", "treatment", normalize_treatment)

    tables = {
        "samples": (samples, "sample_id"),
        "image_measurements": (images, "image_id"),
        "batch_controls": (controls, "control_id"),
    }

    for name, (table, id_column) in tables.items():
        # Save the extra copies before removing exact duplicates.
        duplicates = table.duplicated(keep="first")
        table.loc[duplicates].to_csv(
            RESULTS_DIR / f"{name}_removed_duplicates.csv",
            index=False,
        )

        deduplicated = table.loc[~duplicates].copy()

        # Different records sharing an ID need investigation.
        # Do not silently choose one of them.
        if deduplicated[id_column].duplicated().any():
            raise ValueError(
                f"{name}: conflicting records share {id_column}. "
                "Review before proceeding."
            )

        deduplicated.to_csv(CLEAN_DIR / f"{name}.csv", index=False)

        print(
            f"{name}: {len(table)} input rows, "
            f"{duplicates.sum()} exact duplicates removed, "
            f"{len(deduplicated)} rows saved"
        )

    pd.DataFrame(
        changes,
        columns=["table", "csv_row", "column", "original", "updated"],
    ).to_csv(RESULTS_DIR / "normalization_log.csv", index=False)

    print("\nFormatting changes saved to results/normalization_log.csv")


if __name__ == "__main__":
    main()