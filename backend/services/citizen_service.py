import pandas as pd
from datetime import datetime


def normalize_text(text):
    if pd.isna(text):
        return None

    text = str(text).strip()
    text = text.replace("مالک:", "").strip()
    text = " ".join(text.split())
    return text


def normalize_cnic(cnic):
    if pd.isna(cnic):
        return None

    return str(cnic).strip()


def process_csv_file(file_path, fiscal_year="2026"):
    df = pd.read_csv(file_path, encoding="utf-8-sig")
    df.columns = [col.lower().replace(" ", "_") for col in df.columns]

    if "cnic" not in df.columns:
        raise ValueError("CSV must contain CNIC column.")

    df["cnic"] = df["cnic"].apply(normalize_cnic)

    df["fiscal_year"] = fiscal_year
    df["ingested_at"] = datetime.utcnow()

    text_columns = [
        "full_name",
        "consumer_name",
        "owner_name",
        "buyer_name",
        "reported_address",
        "installation_address",
        "owner_address",
        "property_address"
    ]

    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(normalize_text)

    df = df.dropna(subset=["cnic"])

    return df.to_dict(orient="records")