import re

def standardize_text(text):
    if not text: return ""
    # Convert to string, lowercase, strip whitespace
    text = str(text).lower().strip()
    # Remove special characters
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

def clean_citizen_data(df):
    # Standardize CNIC (Remove dashes)
    df['cnic'] = df['cnic'].astype(str).str.replace('-', '').str.strip()
    # Normalize Names
    df['name'] = df['name'].apply(standardize_text)
    return df