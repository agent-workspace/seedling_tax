from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Transaction, Category, TransactionType
from app.schemas import (
    ReceiptScanResult, InvoiceScanResult, CategorySuggestion,
    MonthlySummaryAI, ImportAnalysisResult,
)

router = APIRouter(prefix="/ai", tags=["ai"])

TENANT_ID = 1


@router.post("/scan-receipt", response_model=ReceiptScanResult)
async def scan_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Scan a receipt image and extract structured data.
    Returns mock data for now; will use Claude Vision API when API key is configured.
    """
    content = await file.read()
    file_size = len(content)
    file_name = file.filename or "unknown"

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Mock response simulating Claude Vision extraction
    return ReceiptScanResult(
        vendor="Office Supplies Ltd",
        date=date.today(),
        total=Decimal("47.99"),
        currency="GBP",
        description=f"Receipt scan from {file_name}",
        suggested_category="Phone, fax, stationery and other office costs",
        confidence=0.85,
        line_items=[
            {"description": "A4 Paper (5 reams)", "amount": "24.99"},
            {"description": "Printer Ink Cartridge", "amount": "18.00"},
            {"description": "Sticky Notes", "amount": "5.00"},
        ],
    )


@router.post("/scan-invoice", response_model=InvoiceScanResult)
async def scan_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Scan an invoice document and extract structured data.
    Returns mock data for now; will use Claude Vision API when API key is configured.
    """
    content = await file.read()
    file_size = len(content)

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    return InvoiceScanResult(
        supplier_name="TechServ Solutions Ltd",
        invoice_number="TS-2026-0042",
        date=date.today(),
        due_date=date(2026, 5, 5),
        total=Decimal("1200.00"),
        currency="GBP",
        line_items=[
            {
                "description": "Web Development Services - March 2026",
                "quantity": "1",
                "unit_price": "1000.00",
                "amount": "1000.00",
            },
            {
                "description": "Hosting and domain renewal",
                "quantity": "1",
                "unit_price": "200.00",
                "amount": "200.00",
            },
        ],
        confidence=0.92,
    )


@router.post("/categorise", response_model=CategorySuggestion)
def categorise_transaction(
    description: str = Form(...),
    amount: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """
    Suggest a category for a transaction based on its description.
    Returns mock data for now; will use Claude API when API key is configured.
    """
    description_lower = description.lower()

    # Simple keyword-based categorisation as placeholder logic
    category_map = {
        "office": ("Phone, fax, stationery and other office costs", "phone_internet"),
        "stationery": ("Phone, fax, stationery and other office costs", "phone_internet"),
        "phone": ("Phone, fax, stationery and other office costs", "phone_internet"),
        "internet": ("Phone, fax, stationery and other office costs", "phone_internet"),
        "broadband": ("Phone, fax, stationery and other office costs", "phone_internet"),
        "software": ("Phone, fax, stationery and other office costs", "phone_internet"),
        "hosting": ("Phone, fax, stationery and other office costs", "phone_internet"),
        "domain": ("Phone, fax, stationery and other office costs", "phone_internet"),
        "fuel": ("Car, van and travel expenses", "car_van"),
        "petrol": ("Car, van and travel expenses", "car_van"),
        "parking": ("Car, van and travel expenses", "car_van"),
        "train": ("Car, van and travel expenses", "car_van"),
        "uber": ("Car, van and travel expenses", "car_van"),
        "travel": ("Car, van and travel expenses", "car_van"),
        "mileage": ("Car, van and travel expenses", "car_van"),
        "rent": ("Rent, rates, power and insurance costs", "rent"),
        "electric": ("Rent, rates, power and insurance costs", "rent"),
        "gas": ("Rent, rates, power and insurance costs", "rent"),
        "water": ("Rent, rates, power and insurance costs", "rent"),
        "insurance": ("Rent, rates, power and insurance costs", "rent"),
        "accountant": ("Accountancy, legal and other professional fees", "accountancy"),
        "legal": ("Accountancy, legal and other professional fees", "accountancy"),
        "solicitor": ("Accountancy, legal and other professional fees", "accountancy"),
        "google ads": ("Advertising and business entertainment costs", "advertising"),
        "facebook ads": ("Advertising and business entertainment costs", "advertising"),
        "marketing": ("Advertising and business entertainment costs", "advertising"),
        "advertising": ("Advertising and business entertainment costs", "advertising"),
        "bank": ("Bank, credit card and other financial charges", "bank_charges"),
        "stripe fee": ("Bank, credit card and other financial charges", "bank_charges"),
        "paypal fee": ("Bank, credit card and other financial charges", "bank_charges"),
        "repair": ("Repairs and maintenance of property and equipment", "repairs"),
        "maintenance": ("Repairs and maintenance of property and equipment", "repairs"),
    }

    suggested_name = "Other business expenses"
    hmrc_code = "other"
    confidence = 0.45
    reasoning = "No strong keyword match found; defaulting to 'Other business expenses'."

    for keyword, (cat_name, code) in category_map.items():
        if keyword in description_lower:
            suggested_name = cat_name
            hmrc_code = code
            confidence = 0.82
            reasoning = f"Matched keyword '{keyword}' in transaction description."
            break

    # Look up category ID from database
    category = (
        db.query(Category)
        .filter(
            Category.tenant_id == TENANT_ID,
            Category.name == suggested_name,
        )
        .first()
    )

    return CategorySuggestion(
        transaction_description=description,
        suggested_category_id=category.id if category else None,
        suggested_category_name=suggested_name,
        confidence=confidence,
        reasoning=reasoning,
    )


@router.post("/monthly-summary", response_model=MonthlySummaryAI)
def generate_monthly_summary(
    year: int = Form(...),
    month: int = Form(...),
    db: Session = Depends(get_db),
):
    """
    Generate an AI-powered monthly summary of financial activity.
    Returns mock data for now; will use Claude API when API key is configured.
    """
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    # Get actual transaction stats for context
    from sqlalchemy import func
    income_total = (
        db.query(func.coalesce(func.sum(Transaction.gbp_amount), 0))
        .filter(
            Transaction.tenant_id == TENANT_ID,
            Transaction.type == TransactionType.income,
            Transaction.date >= start_date,
            Transaction.date < end_date,
            Transaction.is_deleted == False,
        )
        .scalar()
    )

    expense_total = (
        db.query(func.coalesce(func.sum(Transaction.gbp_amount), 0))
        .filter(
            Transaction.tenant_id == TENANT_ID,
            Transaction.type == TransactionType.expense,
            Transaction.date >= start_date,
            Transaction.date < end_date,
            Transaction.is_deleted == False,
        )
        .scalar()
    )

    txn_count = (
        db.query(func.count(Transaction.id))
        .filter(
            Transaction.tenant_id == TENANT_ID,
            Transaction.date >= start_date,
            Transaction.date < end_date,
            Transaction.is_deleted == False,
        )
        .scalar()
    )

    income_val = float(income_total)
    expense_val = float(expense_total)
    net = income_val - expense_val
    month_name = start_date.strftime("%B %Y")

    summary_text = (
        f"In {month_name}, your business recorded {txn_count} transactions. "
        f"Total income was {income_val:,.2f} GBP and total expenses were {expense_val:,.2f} GBP, "
        f"resulting in a net {'profit' if net >= 0 else 'loss'} of {abs(net):,.2f} GBP."
    )

    highlights = []
    if income_val > 0:
        highlights.append(f"Income of {income_val:,.2f} GBP recorded this month.")
    if txn_count > 0:
        highlights.append(f"{txn_count} transactions logged.")

    concerns = []
    if expense_val > income_val and income_val > 0:
        concerns.append("Expenses exceeded income this month.")
    if txn_count == 0:
        concerns.append("No transactions recorded - check if anything is missing.")

    suggestions = [
        "Review uncategorised transactions to ensure accurate tax reporting.",
        "Consider scanning any paper receipts before they fade.",
    ]
    if expense_val > 0:
        suggestions.append("Check if all expenses have receipts attached for HMRC compliance.")

    return MonthlySummaryAI(
        month=month_name,
        summary=summary_text,
        highlights=highlights,
        concerns=concerns,
        suggestions=suggestions,
    )


@router.post("/analyse-import", response_model=ImportAnalysisResult)
async def analyse_import_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Analyse an uploaded CSV/Excel file and suggest column mappings.
    Returns mock data for now; will use Claude API for intelligent mapping when API key is configured.
    """
    content = await file.read()
    file_name = file.filename or "unknown"

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Try to parse the file to get actual column info
    detected_columns = []
    sample_rows = []
    row_count = 0

    try:
        import io
        import csv

        if file_name.endswith((".csv", ".txt")):
            text = content.decode("utf-8", errors="replace")
            reader = csv.reader(io.StringIO(text))
            rows = list(reader)
            if len(rows) > 0:
                headers = rows[0]
                detected_columns = [
                    {"index": i, "name": h.strip(), "sample_values": []}
                    for i, h in enumerate(headers)
                ]
                data_rows = rows[1:]
                row_count = len(data_rows)
                for row in data_rows[:5]:
                    sample_row = {}
                    for i, val in enumerate(row):
                        if i < len(headers):
                            sample_row[headers[i].strip()] = val.strip()
                            if i < len(detected_columns):
                                detected_columns[i]["sample_values"].append(val.strip())
                    sample_rows.append(sample_row)
        elif file_name.endswith((".xlsx", ".xls")):
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
            ws = wb.active
            all_rows = list(ws.iter_rows(values_only=True))
            if len(all_rows) > 0:
                headers = [str(h) if h is not None else f"Column_{i}" for i, h in enumerate(all_rows[0])]
                detected_columns = [
                    {"index": i, "name": h, "sample_values": []}
                    for i, h in enumerate(headers)
                ]
                data_rows = all_rows[1:]
                row_count = len(data_rows)
                for row in data_rows[:5]:
                    sample_row = {}
                    for i, val in enumerate(row):
                        if i < len(headers):
                            str_val = str(val) if val is not None else ""
                            sample_row[headers[i]] = str_val
                            if i < len(detected_columns):
                                detected_columns[i]["sample_values"].append(str_val)
                    sample_rows.append(sample_row)
            wb.close()
    except Exception:
        # If parsing fails, return empty results with a note
        return ImportAnalysisResult(
            detected_columns=[],
            suggested_mappings={},
            sample_rows=[],
            suggested_date_format="%Y-%m-%d",
            row_count=0,
        )

    # Suggest mappings based on column names
    suggested_mappings = {}
    date_keywords = {"date", "transaction date", "posted", "posting date", "value date"}
    description_keywords = {"description", "memo", "narrative", "details", "reference", "payee"}
    amount_keywords = {"amount", "total", "value", "debit", "credit", "sum"}

    for col in detected_columns:
        col_lower = col["name"].lower().strip()
        if col_lower in date_keywords:
            suggested_mappings["date"] = col["name"]
        elif col_lower in description_keywords:
            suggested_mappings["description"] = col["name"]
        elif col_lower in amount_keywords:
            suggested_mappings["amount"] = col["name"]

    # Try to detect date format from samples
    suggested_date_format = "%Y-%m-%d"
    if "date" in suggested_mappings:
        date_col = suggested_mappings["date"]
        for row in sample_rows[:3]:
            sample_date = row.get(date_col, "")
            if "/" in sample_date:
                parts = sample_date.split("/")
                if len(parts) == 3:
                    if len(parts[2]) == 4:
                        if int(parts[0]) > 12:
                            suggested_date_format = "%d/%m/%Y"
                        else:
                            suggested_date_format = "%m/%d/%Y"
                    else:
                        suggested_date_format = "%d/%m/%y"
                break
            elif "-" in sample_date and len(sample_date) == 10:
                suggested_date_format = "%Y-%m-%d"
                break

    return ImportAnalysisResult(
        detected_columns=detected_columns,
        suggested_mappings=suggested_mappings,
        sample_rows=sample_rows,
        suggested_date_format=suggested_date_format,
        row_count=row_count,
    )
