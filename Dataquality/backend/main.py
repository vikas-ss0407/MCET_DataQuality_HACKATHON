from io import BytesIO, StringIO
from typing import Any, Optional

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from engine.data_quality_engine import DataQualityEngine


def sanitize_for_json(obj: Any) -> Any:
    """Convert NaN and other non-JSON-safe types to JSON-compatible values."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, float):
        if np.isnan(obj):
            return None
        elif np.isinf(obj):
            return None
    return obj

app = FastAPI(title="Data Quality Guardian", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = DataQualityEngine()
last_cleaned_df: Optional[pd.DataFrame] = None
last_report: Optional[dict] = None
last_missing_records: Optional[list] = None
last_invalid_records: Optional[list] = None
last_duplicate_records: Optional[list] = None


@app.get("/")
def healthcheck():
    return {"status": "ok", "service": "Data Quality Guardian"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process CSV or Excel file for data quality checks."""
    global last_cleaned_df, last_report, last_missing_records, last_invalid_records, last_duplicate_records

    # Accept CSV and Excel formats
    file_ext = file.filename.lower().split(".")[-1]
    if file_ext not in ["csv", "xlsx", "xls"]:
        raise HTTPException(
            status_code=400, 
            detail="Only CSV and Excel (.xlsx, .xls) files are supported"
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        # Process based on file type
        if file_ext == "csv":
            result = engine.process_csv(content)
        else:  # Excel
            result = engine.process_excel(content)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"Processing error: {str(exc)}") from exc

    # Store cleaned data for download
    last_cleaned_df = pd.DataFrame(result["cleaned_data"])
    last_report = result["report"]
    last_missing_records = result.get("missing_records", [])
    last_invalid_records = result.get("invalid_records", [])
    last_duplicate_records = result.get("duplicate_records", [])

    response_data = {
        "cleaned_data": result["cleaned_data"],
        "report": result["report"],
        "fixes": result["fixes"],
    }
    return sanitize_for_json(response_data)


@app.get("/download/cleaned")
async def download_cleaned():
    if last_cleaned_df is None:
        raise HTTPException(status_code=404, detail="No cleaned dataset available. Upload first.")

    csv_buffer = StringIO()
    last_cleaned_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    headers = {"Content-Disposition": "attachment; filename=cleaned_data.csv"}
    return StreamingResponse(iter([csv_buffer.getvalue()]), media_type="text/csv", headers=headers)


@app.get("/download/excel")
async def download_excel():
    """Download Excel file with multiple sheets: cleaned data, missing, invalid, duplicates."""
    if last_cleaned_df is None:
        raise HTTPException(status_code=404, detail="No cleaned dataset available. Upload first.")

    # Find first non-empty column to use as identifier
    def get_primary_key(df):
        for col in df.columns:
            if df[col].notna().any():
                return col
        return df.columns[0] if len(df.columns) > 0 else "index"
    
    primary_key = get_primary_key(last_cleaned_df)
    
    # Create Excel writer
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Cleaned Data
        last_cleaned_df.to_excel(writer, sheet_name='Cleaned Data', index=False)
        
        # Sheet 2: Missing Fields
        if last_missing_records:
            missing_df = pd.DataFrame(last_missing_records)
            # Add primary key value
            missing_df[primary_key] = missing_df['row_index'].apply(
                lambda idx: last_cleaned_df.iloc[idx][primary_key] if idx < len(last_cleaned_df) else None
            )
            missing_df = missing_df[[primary_key, 'field', 'issue']]
            missing_df.to_excel(writer, sheet_name='Missing Fields', index=False)
        
        # Sheet 3: Invalid Formats
        if last_invalid_records:
            invalid_df = pd.DataFrame(last_invalid_records)
            # Add primary key value
            invalid_df[primary_key] = invalid_df['row_index'].apply(
                lambda idx: last_cleaned_df.iloc[idx][primary_key] if idx < len(last_cleaned_df) else None
            )
            invalid_df = invalid_df[[primary_key, 'field', 'value', 'issue']]
            invalid_df.to_excel(writer, sheet_name='Invalid Formats', index=False)
        
        # Sheet 4: Duplicates
        if last_duplicate_records:
            duplicate_df = pd.DataFrame(last_duplicate_records)
            # Add primary key value and full record
            duplicate_df[primary_key] = duplicate_df['row_index'].apply(
                lambda idx: last_cleaned_df.iloc[idx][primary_key] if idx < len(last_cleaned_df) else None
            )
            # Add all columns from the duplicate records
            for col in last_cleaned_df.columns:
                if col != primary_key:
                    duplicate_df[col] = duplicate_df['row_index'].apply(
                        lambda idx: last_cleaned_df.iloc[idx][col] if idx < len(last_cleaned_df) else None
                    )
            duplicate_df = duplicate_df.drop(columns=['row_index'])
            duplicate_df.to_excel(writer, sheet_name='Duplicates', index=False)
    
    output.seek(0)
    headers = {"Content-Disposition": "attachment; filename=data_quality_report.xlsx"}
    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)


@app.get("/report")
async def get_report():
    if last_report is None:
        raise HTTPException(status_code=404, detail="No report available. Upload first.")
    return last_report
