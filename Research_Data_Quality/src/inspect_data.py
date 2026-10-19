from pathlib import Path

import pandas as pd


# Find the project folder, regardless of where you run the script.
PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "raw"

FILES = {
    "samples": ("samples.csv", "sample_id"),
    "images": ("image_measurements.csv", "image_id"),
    "controls": ("batch_controls.csv", "control_id"),
}


def inspect_table(name, df, id_column):
    """Print an initial overview of one table."""
    print(f"\n{'=' * 60}")
    print(name.upper())
    print("=" * 60)

    print(f"\nRows: {df.shape[0]} | Columns: {df.shape[1]}")

    print("\nFirst five rows:")
    print(df.head().to_string(index=False))

    print("\nColumn types:")
    print(df.dtypes.to_string())

    print("\nMissing values per column:")
    print(df.isna().sum().to_string())

    print(f"\nUnique {id_column} values: {df[id_column].nunique()}")
    print(f"Rows with missing {id_column}: {df[id_column].isna().sum()}")
    print(f"Repeated non-missing IDs: "
          f"{df[id_column].dropna().duplicated().sum()}")

    print(f"Exact duplicate rows: {df.duplicated().sum()}")


def main():
    tables = {}

    for name, (filename, id_column) in FILES.items():
        path = DATA_DIR / filename

        if not path.is_file():
            raise FileNotFoundError(f"Could not find the data file: {path}")

        df = pd.read_csv(path)
        tables[name] = df
        inspect_table(name, df, id_column)

    print("\nExperimental groups as recorded:")
    print(
        tables["samples"]
        .groupby(["treatment", "dose_uM"], dropna=False)
        .size()
        .rename("sample_count")
        .to_string()
    )


if __name__ == "__main__":
    main()