import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def ingest_from_csv(csv_path="complaints.csv", output_path="raw_complaints.parquet"):
    logger.info(f"Loading raw CSV: {csv_path}")

    # Load and normalize column names
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.lower().str.replace(' ', '_')

    # CRITICAL: Drop rows where the narrative is missing or just whitespace
    # This prevents the "garbage in" problem immediately
    initial_count = len(df)
    df = df[df['consumer_complaint_narrative'].notna()]
    df = df[df['consumer_complaint_narrative'].str.strip().str.len() > 10]

    # Save as parquet
    df.to_parquet(output_path, compression="snappy")
    logger.info(f"Ingested {len(df)} valid records (Dropped {initial_count - len(df)} empty rows).")


if __name__ == "__main__":
    ingest_from_csv()