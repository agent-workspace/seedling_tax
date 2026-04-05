from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PAYEEntry
from app.schemas import PAYEEntryCreate, PAYEEntryResponse, PAYESummary, PaginatedResponse

router = APIRouter(prefix="/paye", tags=["paye"])

TENANT_ID = 1


@router.get("", response_model=PaginatedResponse)
def list_paye_entries(
    tax_year: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(PAYEEntry).filter(PAYEEntry.tenant_id == TENANT_ID)

    if tax_year is not None:
        query = query.filter(PAYEEntry.tax_year == tax_year)

    total = query.count()
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    entries = (
        query.order_by(PAYEEntry.tax_year.desc(), PAYEEntry.month.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        items=[PAYEEntryResponse.model_validate(e) for e in entries],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/summary", response_model=PAYESummary)
def get_paye_summary(tax_year: str, db: Session = Depends(get_db)):
    entries = (
        db.query(PAYEEntry)
        .filter(PAYEEntry.tenant_id == TENANT_ID, PAYEEntry.tax_year == tax_year)
        .all()
    )

    total_gross = Decimal("0")
    total_tax = Decimal("0")
    total_ni = Decimal("0")
    total_student = Decimal("0")
    total_other = Decimal("0")

    for entry in entries:
        total_gross += entry.gross_pay
        total_tax += entry.tax_deducted
        total_ni += entry.ni_deducted
        total_student += entry.student_loan
        total_other += entry.other_deductions

    net_pay = total_gross - total_tax - total_ni - total_student - total_other

    return PAYESummary(
        tax_year=tax_year,
        total_gross_pay=total_gross,
        total_tax_deducted=total_tax,
        total_ni_deducted=total_ni,
        total_student_loan=total_student,
        total_other_deductions=total_other,
        net_pay=net_pay,
        months_recorded=len(entries),
    )


@router.get("/{entry_id}", response_model=PAYEEntryResponse)
def get_paye_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = (
        db.query(PAYEEntry)
        .filter(PAYEEntry.id == entry_id, PAYEEntry.tenant_id == TENANT_ID)
        .first()
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="PAYE entry not found")
    return entry


@router.post("", response_model=PAYEEntryResponse, status_code=201)
def create_paye_entry(data: PAYEEntryCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(PAYEEntry)
        .filter(
            PAYEEntry.tenant_id == TENANT_ID,
            PAYEEntry.tax_year == data.tax_year,
            PAYEEntry.month == data.month,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=400,
            detail=f"PAYE entry already exists for month {data.month} of tax year {data.tax_year}",
        )

    entry = PAYEEntry(
        tenant_id=TENANT_ID,
        month=data.month,
        tax_year=data.tax_year,
        gross_pay=data.gross_pay,
        tax_deducted=data.tax_deducted,
        ni_deducted=data.ni_deducted,
        student_loan=data.student_loan,
        other_deductions=data.other_deductions,
        notes=data.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.put("/{entry_id}", response_model=PAYEEntryResponse)
def update_paye_entry(
    entry_id: int, data: PAYEEntryCreate, db: Session = Depends(get_db)
):
    entry = (
        db.query(PAYEEntry)
        .filter(PAYEEntry.id == entry_id, PAYEEntry.tenant_id == TENANT_ID)
        .first()
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="PAYE entry not found")

    entry.month = data.month
    entry.tax_year = data.tax_year
    entry.gross_pay = data.gross_pay
    entry.tax_deducted = data.tax_deducted
    entry.ni_deducted = data.ni_deducted
    entry.student_loan = data.student_loan
    entry.other_deductions = data.other_deductions
    entry.notes = data.notes

    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_paye_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = (
        db.query(PAYEEntry)
        .filter(PAYEEntry.id == entry_id, PAYEEntry.tenant_id == TENANT_ID)
        .first()
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="PAYE entry not found")
    db.delete(entry)
    db.commit()
    return None
