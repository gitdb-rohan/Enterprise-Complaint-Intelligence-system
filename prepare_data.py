import pandas as pd
import numpy as np

def clean_and_prep_rag(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Junk Filter: Remove test/dummy data
    junk_keywords = ["test", "testing", "dummy", "sample", "delete"]
    mask_junk = df['consumer_complaint_narrative'].str.lower().apply(lambda x: any(k in x for k in junk_keywords))
    df = df[~mask_junk].copy()

    # 2. Impute Metadata: Handle missing values for search stability
    impute_map = {
        'state': 'Unknown',
        'company_public_response': 'No public response',
        'company_response_to_consumer': 'No response recorded',
        'submitted_via': 'Web'  # Default
    }
    for col, val in impute_map.items():
        if col in df.columns:
            df[col] = df[col].fillna(val)

    # 3. Intelligence Engineering: Calculate response speed
    df['date_received'] = pd.to_datetime(df['date_received'], errors='coerce')
    df['date_sent_to_company'] = pd.to_datetime(df['date_sent_to_company'], errors='coerce')
    df['days_to_respond'] = (df['date_sent_to_company'] - df['date_received']).dt.days.fillna(0).astype(int)

    return df

def build_full_context(row):
    return (
        f"Product: {row['product']} ({row.get('sub-product', 'N/A')})\n"
        f"Company: {row['company']} | State: {row.get('state', 'Unknown')}\n"
        f"Submitted via: {row.get('submitted_via', 'Unknown')} | Resolution: {row.get('company_response_to_consumer', 'Unknown')}\n"
        f"Response Time: {row.get('days_to_respond', 0)} days\n"
        f"Complaint Narrative: {row['consumer_complaint_narrative']}"
    )

def main():
    print("Loading complaints_sample_2000.csv...")
    df = pd.read_csv("complaints_sample_2000.csv")
    
    # Normalize columns to match expected lowercase format
    df.columns = df.columns.str.lower().str.replace(' ', '_')
    
    # Split the dataset
    mask_has_narrative = df['consumer_complaint_narrative'].notna()
    
    df_rag = df[mask_has_narrative].copy()
    df_portfolio = df[~mask_has_narrative].copy()
    
    print(f"Total Records: {len(df)}")
    print(f"RAG Records (with narrative): {len(df_rag)}")
    print(f"Portfolio Records (without narrative): {len(df_portfolio)}")
    
    # Prepare RAG data
    print("Processing RAG data...")
    df_rag = clean_and_prep_rag(df_rag)
    df_rag['full_context'] = df_rag.apply(build_full_context, axis=1)
    
    df_rag.to_parquet("processed_complaints.parquet", compression="snappy")
    print("Saved processed_complaints.parquet")
    
    # Prepare Portfolio data (we can just save the subset directly, 
    # maybe parse dates to make visualization easier later)
    print("Processing Portfolio data...")
    df_portfolio['date_received'] = pd.to_datetime(df_portfolio['date_received'], errors='coerce')
    df_portfolio.to_parquet("portfolio_data.parquet", compression="snappy")
    print("Saved portfolio_data.parquet")

if __name__ == "__main__":
    main()
