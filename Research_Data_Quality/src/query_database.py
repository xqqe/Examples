from pathlib import Path
import sqlite3

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_DIR / "data" / "processed" / "research.db"


def main():
    if not DATABASE_PATH.is_file():
        raise FileNotFoundError("Run build_database.py first.")

    query = """
        SELECT
            s.sample_id,
            s.batch_id,
            s.treatment,
            s.dose_uM,
            w.n_fields_fluorescence,
            w.mean_fluorescence_au
        FROM samples AS s
        JOIN well_summary AS w
            ON s.sample_id = w.sample_id
        WHERE w.n_fields_fluorescence < 4
        ORDER BY s.batch_id, s.sample_id;
    """

    with sqlite3.connect(DATABASE_PATH) as connection:
        result = pd.read_sql_query(query, connection)

    print(result.to_string(index=False))


if __name__ == "__main__":
    main()