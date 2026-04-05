import io
import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ImportProfile, Transaction, TransactionType, TransactionSource, ImportTargetType
from app.schemas import ImportProfileCreate, ImportProfileResponse, PaginatedResponse, TransactionResponse

router = APIRouter(prefix="/imports", tags=["imports"])

TENANT_ID = 1


# ---- Import Profiles ----

@router.get("/profiles", response_model=list[ImportProfileResponse])
def list_import_profiles(db: Session = Depends(get_db)):
    profiles = (
        db.query(ImportProfile)
        .filter(ImportProfile.tenant_id == TENANT_ID)
        .order_by(ImportProfile.name)
        .all()
    )
    return profiles


@router.get("/profiles/{profile_id}", response_model=ImportProfileResponse)
def get_import_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = (
        db.query(ImportProfile)
        .filter(ImportProfile.id == profile_id, ImportProfile.tenant_id == TENANT_ID)
        .first()
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Import profile not found")
    return profile


@router.post("/profiles", response_model=ImportProfileResponse, status_code=201)
def create_import_profile(data: ImportProfileCreate, db: Session = Depends(get_db)):
    profile = ImportProfile(
        tenant_id=TENANT_ID,
        name=data.name,
        column_mappings=data.column_mappings,
        skip_rows=data.skip_rows,
        date_format=data.date_format,
        target_type=data.target_type,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/profiles/{profile_id}", response_model=ImportProfileResponse)
def update_import_profile(
    profile_id: int, data: ImportProfileCreate, db: Session = Depends(get_db)
):
    profile = (
        db.query(ImportProfile)
        .filter(ImportProfile.id == profile_id, ImportProfile.tenant_id == TENANT_ID)
        .first()
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Import profile not found")

    profile.name = data.name
    profile.column_mappings = data.column_mappings
    profile.skip_rows = data.skip_rows
    profile.date_format = data.date_format
    profile.target_type = data.target_type

    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/profiles/{profile_id}", status_code=204)
def delete_import_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = (
        db.query(ImportProfile)
        .filter(ImportProfile.id == profile_id, ImportProfile.tenant_id == TENANT_ID)
        .first()
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Import profile not found")
    db.delete(profile)
    db.commit()
    return None


# ---- Import Processing ----

def _parse_csv(content: bytes, skip_rows: int) -> list[dict]:
    """Parse CSV content into a list of dicts."""
    text = content.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    if skip_rows > 0:
        rows = rows[skip_rows:]

    if len(rows) < 2:
        return []

    headers = [h.strip() for h in rows[0]]
    result = []
    for row in rows[1:]:
        if len(row) == 0 or all(cell.strip() == "" for cell in row):
            continue
        row_dict = {}
        for i, val in enumerate(row):
            if i < len(headers):
                row_dict[headers[i]] = val.strip()
        result.append(row_dict)
    return result


def _parse_excel(content: bytes, skip_rows: int) -> list[dict]:
    """Parse Excel content into a list of dicts."""
    import openpyxl

    wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
    ws = wb.active
    all_rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if skip_rows > 0:
        all_rows = all_rows[skip_rows:]

    if len(all_rows) < 2:
        return []

    headers = [str(h).strip() if h is not None else f"Column_{i}" for i, h in enumerate(all_rows[0])]
    result = []
    for row in all_rows[1:]:
        if all(cell is None or str(cell).strip() == "" for cell in row):
            continue
        row_dict = {}
        for i, val in enumerate(row):
            if i < len(headers):
                row_dict[headers[i]] = str(val).strip() if val is not None else ""
        result.append(row_dict)
    return result


@router.post("/upload")
async def upload_and_process(
    file: UploadFile = File(...),
    profile_id: int = Form(...),
    dry_run: bool = Form(False),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV or Excel file and process it using the specified import profile.
    If dry_run=True, returns a preview without creating transactions.
    """
    profile = (
        db.query(ImportProfile)
        .filter(ImportProfile.id == profile_id, ImportProfile.tenant_id == TENANT_ID)
        .first()
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Import profile not found")

    content = await file.read()
    file_name = file.filename or "unknown"

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Parse file
    if file_name.endswith((".xlsx", ".xls")):
        rows = _parse_excel(content, profile.skip_rows)
    elif file_name.endswith((".csv", ".txt")):
        rows = _parse_csv(content, profile.skip_rows)
    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload CSV or Excel files.",
        )

    if len(rows) == 0:
        return {
            "message": "No data rows found in file",
            "imported": 0,
            "skipped": 0,
            "errors": [],
        }

    mappings = profile.column_mappings
    date_col = mappings.get("date")
    description_col = mappings.get("description")
    amount_col = mappings.get("amount")
    category_col = mappings.get("category")
    notes_col = mappings.get("notes")
    currency_col = mappings.get("currency")

    if date_col is None or description_col is None or amount_col is None:
        raise HTTPException(
            status_code=400,
            detail="Import profile must map at least 'date', 'description', and 'amount' columns.",
        )

    imported = 0
    skipped = 0
    errors = []
    preview_rows = []

    for i, row in enumerate(rows):
        row_num = i + 1 + profile.skip_rows + 1  # Account for header and skipped rows

        # Parse date
        date_str = row.get(date_col, "").strip()
        if not date_str:
            errors.append({"row": row_num, "error": "Missing date value"})
            skipped += 1
            continue

        try:
            parsed_date = datetime.strptime(date_str, profile.date_format).date()
        except ValueError:
            errors.append({"row": row_num, "error": f"Invalid date format: '{date_str}'"})
            skipped += 1
            continue

        # Parse description
        description = row.get(description_col, "").strip()
        if not description:
            errors.append({"row": row_num, "error": "Missing description"})
            skipped += 1
            continue

        # Parse amount
        amount_str = row.get(amount_col, "").strip()
        amount_str = amount_str.replace(",", "").replace("£", "").replace("$", "").replace("€", "")
        if not amount_str:
            errors.append({"row": row_num, "error": "Missing amount"})
            skipped += 1
            continue

        try:
            amount = Decimal(amount_str)
        except InvalidOperation:
            errors.append({"row": row_num, "error": f"Invalid amount: '{amount_str}'"})
            skipped += 1
            continue

        # Handle negative amounts: negative = expense, positive = income (or use profile target_type)
        txn_type = str(profile.target_type.value) if hasattr(profile.target_type, "value") else str(profile.target_type)
        abs_amount = abs(amount)

        currency = "GBP"
        if currency_col and currency_col in row:
            currency = row[currency_col].strip().upper() or "GBP"

        notes = ""
        if notes_col and notes_col in row:
            notes = row[notes_col].strip()

        if dry_run:
            preview_rows.append({
                "row": row_num,
                "date": str(parsed_date),
                "description": description,
                "amount": str(abs_amount),
                "type": txn_type,
                "currency": currency,
                "notes": notes,
            })
            imported += 1
        else:
            txn = Transaction(
                tenant_id=TENANT_ID,
                type=txn_type,
                date=parsed_date,
                description=description,
                source="import",
                original_amount=abs_amount,
                currency=currency,
                exchange_rate=Decimal("1.0"),
                gbp_amount=abs_amount,
                notes=notes if notes else None,
                import_profile_id=profile.id,
            )
            db.add(txn)
            imported += 1

    if not dry_run and imported > 0:
        db.commit()

    result = {
        "message": f"{'Preview: ' if dry_run else ''}{imported} transactions {'would be ' if dry_run else ''}imported, {skipped} skipped",
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:50],  # Limit error output
        "total_rows": len(rows),
    }

    if dry_run:
        result["preview"] = preview_rows[:20]

    return result
