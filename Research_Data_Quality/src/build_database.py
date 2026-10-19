from pathlib import Path
import sqlite3

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_DIR / "data" / "processed"
DATABASE_PATH = DATA_DIR / "research.db"


def main():
    files = {
        "samples": DATA_DIR / "samples.csv",
        "images": DATA_DIR / "images_with_batch_qc.csv",
        "batch_qc": PROJECT_DIR / "results" / "batch_qc.csv",
        "well_summary": DATA_DIR / "well_summary.csv",
    }

    with sqlite3.connect(DATABASE_PATH) as connection:
        for table_name, path in files.items():
            table = pd.read_csv(path)

            table.to_sql(
                table_name,
                connection,
                if_exists="replace",
                index=False,
            )

            print(f"Loaded {table_name}: {len(table)} rows")

        # Unique indexes reject repeated identifiers.
        connection.executescript("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_samples_id
                ON samples(sample_id);

            CREATE UNIQUE INDEX IF NOT EXISTS idx_images_id
                ON images(image_id);

            CREATE UNIQUE INDEX IF NOT EXISTS idx_batch_id
                ON batch_qc(batch_id);

            CREATE UNIQUE INDEX IF NOT EXISTS idx_well_id
                ON well_summary(sample_id);
        """)

        query = """
            SELECT
                batch_id,
                treatment,
                dose_uM,
                COUNT(*) AS number_of_wells
            FROM samples
            GROUP BY batch_id, treatment, dose_uM
            ORDER BY batch_id, dose_uM;
        """

        result = pd.read_sql_query(query, connection)

        print("\nWells by batch and treatment:")
        print(result.to_string(index=False))

    print(f"\nDatabase saved to: {DATABASE_PATH}")


if __name__ == "__main__":
    main()