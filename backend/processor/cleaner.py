import re
import pandas as pd


def standardize_text(text):
    if pd.isna(text) or text is None:
        return ""

    text = str(text).strip()
    text = text.replace("مالک:", "").strip()
    text = text.replace("جناب", "").strip()
    text = text.replace("Mr.", "").strip()
    text = text.replace("Sahib", "").strip()
    text = re.sub(r"\s+", " ", text)

    return text


def normalize_cnic(cnic):
    if pd.isna(cnic) or cnic is None:
        return ""

    return str(cnic).strip()


def clean_citizen_data(df):
    df.columns = [col.lower().strip().replace(" ", "_") for col in df.columns]

    if "cnic" in df.columns:
        df["cnic"] = df["cnic"].apply(normalize_cnic)

    text_columns = [
        "name",
        "full_name",
        "owner_name",
        "consumer_name",
        "buyer_name",
        "reported_address",
        "owner_address",
        "installation_address",
        "property_address"
    ]

    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(standardize_text)

    return df