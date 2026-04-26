"""
Export Utilities
Handles data export to Excel and CSV formats.
"""

import pandas as pd
from sqlalchemy.orm import Session
from models import Record
from typing import List
from io import BytesIO

def records_to_dataframe(records: List[Record]) -> pd.DataFrame:
    """Convert SQLAlchemy records to Pandas DataFrame."""
    if not records:
        return pd.DataFrame()

    data = []
    for r in records:
        data.append({
            "ID": r.id,
            "Name": r.name,
            "Email": r.email,
            "Phone": r.phone,
            "Category": r.category,
            "Amount": r.amount,
            "Date": r.date.strftime("%Y-%m-%d") if r.date else None,
            "Status": r.status,
            "Notes": r.notes,
            "Created At": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else None,
            "Updated At": r.updated_at.strftime("%Y-%m-%d %H:%M") if r.updated_at else None,
        })

    return pd.DataFrame(data)

def export_to_csv(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to CSV bytes for download."""
    return df.to_csv(index=False).encode('utf-8')

def export_to_excel(df: pd.DataFrame) -> bytes:
    """Convert DataFrame to Excel bytes for download."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Records')

        # Auto-adjust column widths
        worksheet = writer.sheets['Records']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)
    return output.getvalue()
