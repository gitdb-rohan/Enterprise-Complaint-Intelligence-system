import os
import time
import logging
import requests
import pandas as pd
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def get_resilient_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))
    return session


def fetch_and_save_raw(total_records: int = 2000, batch_size: int = 100, output_path: str = "raw_complaints.parquet"):
    url = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
    all_records = []
    session = get_resilient_session()

    for offset in range(0, total_records, batch_size):
        logger.info(f"Extracting batch: offset={offset}, limit={batch_size}")
        params = {"size": batch_size, "from": offset, "has_narrative": "true", "format": "json"}

        try:
            response = session.get(url, params=params, timeout=30)
            response.raise_for_status()
            hits = response.json().get("hits", {}).get("hits", [])
            all_records.extend([hit["_source"] for hit in hits])
            time.sleep(0.5)
        except requests.exceptions.RequestException as e:
            logger.error(f"Batch failed at offset {offset}: {e}")
            break


    df = pd.DataFrame(all_records)

    # --- CRITICAL VERIFICATION STEP 1 ---
    print("\n" + "=" * 40 + "\nVERIFICATION: DATA EXTRACTION STATUS\n" + "=" * 40)
    print(f"Total Rows Extracted: {df.shape[0]}")
    print(f"Total Columns Extracted: {df.shape[1]}")

    # GUARD CLAUSE: Prevent saving an empty DataFrame
    if df.empty:
        logger.error("Critical Failure: No data extracted from API. Aborting disk write to prevent corruption.")
        print("=" * 40 + "\n")
        return

    print("\n--- Exact RAM Consumption Footprint ---")
    df.info(memory_usage="deep")
    print("=" * 40 + "\n")

    # Persist directly to disk
    df.to_parquet(output_path, compression="snappy")
    logger.info(f"Raw data successfully checkpointed to disk at: {output_path}")

if __name__ == "__main__":
    fetch_and_save_raw(total_records=2000, batch_size=10)