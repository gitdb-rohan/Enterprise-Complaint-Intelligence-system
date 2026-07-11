import os
import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize MCP Server
mcp = FastMCP("Complaint Intelligence Server")

def get_chroma_collection():
    client = chromadb.PersistentClient(path="./complaint_db")
    gemini_ef = embedding_functions.GoogleGeminiEmbeddingFunction()
    return client.get_collection(
        name="complaint_intelligence",
        embedding_function=gemini_ef
    )

@mcp.tool()
def search_complaints(query: str, limit: int = 5) -> str:
    """
    Search historical consumer complaints stored in the local vector database.
    Use this tool to find evidence of past issues based on a topic or query.
    
    Args:
        query: The topic or issue to search for (e.g., 'unexpected late fees')
        limit: The number of results to return (default 5)
    """
    try:
        collection = get_chroma_collection()
        results = collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        docs = results.get('documents')
        if not docs or not docs[0]:
            return "No matching complaints found."
            
        return "\n\n---\n\n".join(docs[0])
    except Exception as e:
        return f"Error searching vector database: {str(e)}"

@mcp.tool()
def get_portfolio_stats() -> str:
    """
    Get aggregated statistics about the non-narrative complaint dataset.
    Returns metrics like total complaints, unique products, and top 5 companies.
    """
    try:
        df = pd.read_parquet("portfolio_data.parquet")
        
        total = len(df)
        products = df['product'].nunique()
        companies = df['company'].nunique()
        
        top_companies = df['company'].value_counts().head(5).to_dict()
        top_products = df['product'].value_counts().head(5).to_dict()
        
        stats = f"""Portfolio Statistics:
- Total Complaints (without narratives): {total}
- Unique Products: {products}
- Unique Companies: {companies}

Top 5 Companies:
{top_companies}

Top 5 Products:
{top_products}
"""
        return stats
    except Exception as e:
        return f"Error loading portfolio data: {str(e)}"

if __name__ == "__main__":
    # Start the FastMCP server on standard I/O for client connections
    mcp.run(transport='stdio')
