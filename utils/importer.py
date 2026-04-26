"""
Import Utilities
Handles bulk data import from Excel and CSV files.
"""

import pandas as pd
import streamlit as st
from datetime import datetime
from typing import List, Dict, Tuple

REQUIRED_COLUMNS = ["name", "category"]
OPTIONAL_COLUMNS = ["email", "phone", "amount", "date", "status", "notes"]
VALID_STATUSES = {"active", "inactive", "pending"}

def validate_file(file) -> Tuple[bool, str, pd.DataFrame]:
    """
    Validate uploaded file and return DataFrame.
    Returns: (is_valid, message, dataframe)
    """
    try:
        # Read file based on extension
        file_name = file.name.lower()
        if file_name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file_name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            return False, "❌ Unsupported file format. Use .csv or .xlsx", pd.DataFrame()

        if df.empty:
            return False, "❌ File is empty", pd.DataFrame()

        # Clean column names (lowercase, strip spaces)
        df.columns = df.columns.str.lower().str.strip()

        # Check required columns
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            return False, f"❌ Missing required columns: {', '.join(missing)}", pd.DataFrame()

        return True, f"✅ File loaded: {len(df)} rows, {len(df.columns)} columns", df

    except Exception as e:
        return False, f"❌ Error reading file: {str(e)}", pd.DataFrame()

def clean_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Clean and validate DataFrame data.
    Returns: (cleaned_df, warnings)
    """
    warnings = []
    df = df.copy()

    # Remove completely empty rows
    df = df.dropna(how='all')

    # Ensure required fields are not null
    df = df.dropna(subset=["name", "category"])

    if len(df) == 0:
        return df, ["❌ No valid rows found after cleaning"]

    # Clean text fields
    for col in ["name", "email", "phone", "category", "status", "notes"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace('nan', None).replace('None', None)

    # Validate status
    if "status" in df.columns:
        invalid_statuses = df[~df["status"].isin(VALID_STATUSES | {None, 'nan', 'None'})]["status"].unique()
        if len(invalid_statuses) > 0:
            warnings.append(f"⚠️ Invalid statuses found: {', '.join(map(str, invalid_statuses))}. Setting to 'active'.")
            df.loc[~df["status"].isin(VALID_STATUSES), "status"] = "active"
    else:
        df["status"] = "active"

    # Clean amount
    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors='coerce').fillna(0.0)
        df["amount"] = df["amount"].clip(lower=0)
    else:
        df["amount"] = 0.0

    # Parse date
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors='coerce')
        invalid_dates = df["date"].isna().sum()
        if invalid_dates > 0:
            warnings.append(f"⚠️ {invalid_dates} rows had invalid dates (set to NULL)")
    else:
        df["date"] = None

    # Remove rows with empty names after cleaning
    initial_count = len(df)
    df = df[df["name"].notna() & (df["name"] != '')]
    dropped = initial_count - len(df)
    if dropped > 0:
        warnings.append(f"⚠️ Dropped {dropped} rows with empty names")

    return df, warnings

def dataframe_to_records(df: pd.DataFrame) -> List[Dict]:
    """Convert cleaned DataFrame to list of dicts for database insertion."""
    records = []
    for _, row in df.iterrows():
        record = {
            "name": row["name"],
            "category": row["category"],
            "email": row.get("email") if pd.notna(row.get("email")) else None,
            "phone": row.get("phone") if pd.notna(row.get("phone")) else None,
            "amount": float(row.get("amount", 0)) if pd.notna(row.get("amount")) else 0.0,
            "date": row["date"].to_pydatetime() if pd.notna(row.get("date")) else None,
            "status": row.get("status", "active"),
            "notes": row.get("notes") if pd.notna(row.get("notes")) else None,
        }
        records.append(record)
    return records

def generate_template() -> pd.DataFrame:
    """Generate a sample template file for users."""
    data = {
        "name": ["John Doe", "Jane Smith", "Bob Johnson"],
        "email": ["john@example.com", "jane@example.com", "bob@example.com"],
        "phone": ["+92-300-1234567", "+92-301-7654321", "+92-302-1122334"],
        "category": ["Customer", "Vendor", "Partner"],
        "amount": [1500.00, 2500.50, 0.00],
        "date": ["2026-04-20", "2026-04-21", "2026-04-22"],
        "status": ["active", "active", "pending"],
        "notes": ["First contact", "Regular client", "New lead"]
    }
    return pd.DataFrame(data)
