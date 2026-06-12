import pandas as pd
from unidecode import unidecode
from datetime import datetime

def normalize_text(text):
    if pd.isna(text): return None
    return unidecode(str(text)).strip().upper()

def process_csv_file(file_path, fiscal_year="2026"):
    df = pd.read_csv(file_path)
    df.columns = [col.lower().replace(" ", "_") for col in df.columns]
    
    # Standardize CNIC
    df['cnic'] = df['cnic'].astype(str).str.replace('-', '').str.strip()
    
    # Add metadata for historical tracking
    df['fiscal_year'] = fiscal_year
    df['ingested_at'] = datetime.utcnow()
    
    # Normalize names
    for col in ['full_name', 'consumer_name', 'owner_name']:
        if col in df.columns:
            df[col] = df[col].apply(normalize_text)
            
    return df.to_dict(orient='records')