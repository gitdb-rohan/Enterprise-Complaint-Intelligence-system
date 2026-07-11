import os
import logging
import pandas as pd
from dotenv import load_dotenv
import chromadb
from chromadb.utils import embedding_functions

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("System Missing Environment Variable: GEMINI_API_KEY")


def ingest_to_vector_store(input_path: str = "processed_complaints.parquet", db_dir: str = "./complaint_db"):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Missing input dependency. Run process.py first. Missing: {input_path}")

    logger.info(f"Loading processed context data from disk: {input_path}")
    df = pd.read_parquet(input_path)

    logger.info("Connecting to Local Persistent ChromaDB Storage...")
    chroma_client = chromadb.PersistentClient(path=db_dir)

    gemini_ef = embedding_functions.GoogleGeminiEmbeddingFunction()

    # Re-create/get collection cleanly
    collection = chroma_client.get_or_create_collection(
        name="complaint_intelligence",
        embedding_function=gemini_ef
    )

    logger.info("Streaming data vectors into local disk partition...")
    # Prepare payloads
    documents = df["full_context"].tolist()
    ids = [f"id_{i}" for i in range(len(df))]
    metadatas = [
        {
            "product": str(row.get("product", "Unknown")),
            "company": str(row.get("company", "Unknown")),
            "complaint_id": str(row.get("complaint_id", "Unknown"))
        }
        for _, row in df.iterrows()
    ]

    import time
    step = 50
    for i in range(0, len(documents), step):
        logger.info(f"Indexing vector chunk: {i} to {i + step}")
        collection.add(
            documents=documents[i:i + step],
            metadatas=metadatas[i:i + step],
            ids=ids[i:i + step]
        )
        time.sleep(15)

    # --- CRITICAL VERIFICATION STEP 3 ---
    print("\n" + "=" * 40 + "\nVERIFICATION: VECTOR STORE DIAGNOSTICS\n" + "=" * 40)
    indexed_count = collection.count()
    print(f"Total Vector Collections Registered: {indexed_count}")

    print("\n--- Inspecting First Raw Payload Inside Chroma Storage ---")
    peek_data = collection.peek(limit=1)
    print(f"Peek Document Content:\n{peek_data['documents'][0]}")
    print(f"Peek Metadata Content: {peek_data['metadatas'][0]}")
    print("=" * 40 + "\n")


if __name__ == "__main__":
    ingest_to_vector_store()