from pathlib import Path
import sqlite3

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_DIR / "data" / "processed" / "research.db"
QUERY_PATH = PROJECT_DIR / "sql" / "paired_fluorescence.sql"
RESULTS_DIR = PROJECT_DIR / "results"


def main():
    if not DATABASE_PATH.is_file():
        raise FileNotFoundError("Run build_database.py first.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    query = QUERY_PATH.read_text(encoding="utf-8")

    with sqlite3.connect(DATABASE_PATH) as connection:
        pairs = pd.read_sql_query(query, connection)

    if pairs.empty:
        raise ValueError("No treatment–vehicle pairs met the criteria.")

    pairs.to_csv(
        RESULTS_DIR / "paired_fluorescence.csv",
        index=False,
    )

    summary = (
        pairs.groupby("dose_uM")
        .agg(
            n_pairs=("treated_sample_id", "count"),
            n_valid_ratios=("fluorescence_fold_change", "count"),
            n_batches=("batch_id", "nunique"),
            mean_fold_change=("fluorescence_fold_change", "mean"),
            median_fold_change=("fluorescence_fold_change", "median"),
            mean_difference=("fluorescence_difference", "mean"),
        )
        .reset_index()
    )

    summary.to_csv(
        RESULTS_DIR / "paired_fluorescence_summary.csv",
        index=False,
    )

    print("\nPaired fluorescence summary:")
    print(summary.round(3).to_string(index=False))


if __name__ == "__main__":
    main()