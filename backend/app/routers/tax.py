from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Transaction, TransactionType, TaxYear
from app.schemas import TaxSummary

router = APIRouter(prefix="/tax", tags=["tax"])

TENANT_ID = 1

# 2026/27 UK Tax rates
PERSONAL_ALLOWANCE = Decimal("12570")
BASIC_RATE_LIMIT = Decimal("50270")
HIGHER_RATE_LIMIT = Decimal("125140")

BASIC_RATE = Decimal("0.20")
HIGHER_RATE = Decimal("0.40")
ADDITIONAL_RATE = Decimal("0.45")

# Class 2 NI
CLASS_2_WEEKLY = Decimal("3.45")
CLASS_2_WEEKS = 52
CLASS_2_THRESHOLD = Decimal("12570")

# Class 4 NI
CLASS_4_LOWER = Decimal("12570")
CLASS_4_UPPER = Decimal("50270")
CLASS_4_MAIN_RATE = Decimal("0.06")
CLASS_4_HIGHER_RATE = Decimal("0.02")


def _tax_year_dates(year_label: str) -> tuple[date, date]:
    """Parse year label like '2026/27' into start and end dates."""
    parts = year_label.split("/")
    start_year = int(parts[0])
    start = date(start_year, 4, 6)
    end = date(start_year + 1, 4, 5)
    return start, end


def _calculate_income_tax(taxable_profit: Decimal) -> tuple[Decimal, list[dict]]:
    """Calculate income tax based on UK bands. Returns total tax and breakdown."""
    if taxable_profit <= 0:
        return Decimal("0"), []

    breakdown = []
    remaining = taxable_profit
    total_tax = Decimal("0")

    # Personal allowance (tapers above £100k)
    personal_allowance = PERSONAL_ALLOWANCE
    if taxable_profit > Decimal("100000"):
        reduction = (taxable_profit - Decimal("100000")) / 2
        personal_allowance = max(Decimal("0"), PERSONAL_ALLOWANCE - reduction)

    # Apply personal allowance
    if remaining <= personal_allowance:
        breakdown.append({
            "band": "Personal Allowance",
            "rate": "0%",
            "income": str(remaining.quantize(Decimal("0.01"))),
            "tax": "0.00",
        })
        return Decimal("0"), breakdown

    breakdown.append({
        "band": "Personal Allowance",
        "rate": "0%",
        "income": str(personal_allowance.quantize(Decimal("0.01"))),
        "tax": "0.00",
    })
    remaining -= personal_allowance

    # Basic rate: income from PA to £50,270
    basic_band = BASIC_RATE_LIMIT - PERSONAL_ALLOWANCE
    if personal_allowance < PERSONAL_ALLOWANCE:
        basic_band = BASIC_RATE_LIMIT - personal_allowance

    basic_taxable = min(remaining, basic_band)
    if basic_taxable > 0:
        basic_tax = (basic_taxable * BASIC_RATE).quantize(Decimal("0.01"), ROUND_HALF_UP)
        total_tax += basic_tax
        breakdown.append({
            "band": "Basic Rate",
            "rate": "20%",
            "income": str(basic_taxable.quantize(Decimal("0.01"))),
            "tax": str(basic_tax),
        })
        remaining -= basic_taxable

    # Higher rate: £50,271 to £125,140
    higher_band = HIGHER_RATE_LIMIT - BASIC_RATE_LIMIT
    higher_taxable = min(remaining, higher_band)
    if higher_taxable > 0:
        higher_tax = (higher_taxable * HIGHER_RATE).quantize(Decimal("0.01"), ROUND_HALF_UP)
        total_tax += higher_tax
        breakdown.append({
            "band": "Higher Rate",
            "rate": "40%",
            "income": str(higher_taxable.quantize(Decimal("0.01"))),
            "tax": str(higher_tax),
        })
        remaining -= higher_taxable

    # Additional rate: over £125,140
    if remaining > 0:
        additional_tax = (remaining * ADDITIONAL_RATE).quantize(Decimal("0.01"), ROUND_HALF_UP)
        total_tax += additional_tax
        breakdown.append({
            "band": "Additional Rate",
            "rate": "45%",
            "income": str(remaining.quantize(Decimal("0.01"))),
            "tax": str(additional_tax),
        })

    return total_tax, breakdown


def _calculate_class2_ni(taxable_profit: Decimal) -> Decimal:
    """Class 2 NI: £3.45/week if profits > £12,570."""
    if taxable_profit > CLASS_2_THRESHOLD:
        return (CLASS_2_WEEKLY * CLASS_2_WEEKS).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return Decimal("0")


def _calculate_class4_ni(taxable_profit: Decimal) -> Decimal:
    """Class 4 NI: 6% on £12,570-£50,270, 2% above £50,270."""
    if taxable_profit <= CLASS_4_LOWER:
        return Decimal("0")

    total_ni = Decimal("0")

    # Main rate band
    main_band_income = min(taxable_profit, CLASS_4_UPPER) - CLASS_4_LOWER
    if main_band_income > 0:
        total_ni += (main_band_income * CLASS_4_MAIN_RATE).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )

    # Higher rate
    if taxable_profit > CLASS_4_UPPER:
        higher_income = taxable_profit - CLASS_4_UPPER
        total_ni += (higher_income * CLASS_4_HIGHER_RATE).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )

    return total_ni


@router.get("/summary", response_model=TaxSummary)
def get_tax_summary(
    tax_year: str = "2026/27",
    db: Session = Depends(get_db),
):
    """Calculate full tax summary for the given tax year."""
    start_date, end_date = _tax_year_dates(tax_year)

    # Total income
    income_result = (
        db.query(func.coalesce(func.sum(
            Transaction.gbp_amount * Transaction.allowable_percentage / 100
        ), 0))
        .filter(
            Transaction.tenant_id == TENANT_ID,
            Transaction.type == TransactionType.income,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.is_deleted == False,
        )
        .scalar()
    )
    gross_income = Decimal(str(income_result)).quantize(Decimal("0.01"), ROUND_HALF_UP)

    # Total expenses
    expense_result = (
        db.query(func.coalesce(func.sum(
            Transaction.gbp_amount * Transaction.allowable_percentage / 100
        ), 0))
        .filter(
            Transaction.tenant_id == TENANT_ID,
            Transaction.type == TransactionType.expense,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.is_deleted == False,
        )
        .scalar()
    )
    total_expenses = Decimal(str(expense_result)).quantize(Decimal("0.01"), ROUND_HALF_UP)

    taxable_profit = max(Decimal("0"), gross_income - total_expenses)

    income_tax, breakdown = _calculate_income_tax(taxable_profit)
    ni_class2 = _calculate_class2_ni(taxable_profit)
    ni_class4 = _calculate_class4_ni(taxable_profit)
    total_tax = income_tax + ni_class2 + ni_class4

    effective_rate = Decimal("0")
    if taxable_profit > 0:
        effective_rate = (total_tax / taxable_profit * 100).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )

    return TaxSummary(
        tax_year=tax_year,
        gross_income=gross_income,
        total_expenses=total_expenses,
        taxable_profit=taxable_profit,
        personal_allowance=PERSONAL_ALLOWANCE,
        income_tax=income_tax,
        ni_class2=ni_class2,
        ni_class4=ni_class4,
        total_tax=total_tax,
        effective_rate=effective_rate,
        income_tax_breakdown=breakdown,
    )


@router.get("/self-assessment")
def generate_self_assessment_data(
    tax_year: str = "2026/27",
    db: Session = Depends(get_db),
):
    """Generate data structured for SA103 (Self Employment) supplementary pages."""
    start_date, end_date = _tax_year_dates(tax_year)

    # Get income by category
    income_rows = (
        db.query(
            Transaction.category_id,
            func.sum(Transaction.gbp_amount * Transaction.allowable_percentage / 100).label("total"),
        )
        .filter(
            Transaction.tenant_id == TENANT_ID,
            Transaction.type == TransactionType.income,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.is_deleted == False,
        )
        .group_by(Transaction.category_id)
        .all()
    )

    # Get expenses by category
    expense_rows = (
        db.query(
            Transaction.category_id,
            func.sum(Transaction.gbp_amount * Transaction.allowable_percentage / 100).label("total"),
        )
        .filter(
            Transaction.tenant_id == TENANT_ID,
            Transaction.type == TransactionType.expense,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.is_deleted == False,
        )
        .group_by(Transaction.category_id)
        .all()
    )

    gross_income = sum(Decimal(str(row.total)) for row in income_rows)
    total_expenses = sum(Decimal(str(row.total)) for row in expense_rows)
    net_profit = gross_income - total_expenses

    income_tax, _ = _calculate_income_tax(max(Decimal("0"), net_profit))
    ni_class2 = _calculate_class2_ni(max(Decimal("0"), net_profit))
    ni_class4 = _calculate_class4_ni(max(Decimal("0"), net_profit))

    sa_data = {
        "tax_year": tax_year,
        "sa103": {
            "business_description": "To be completed",
            "accounting_period_start": str(start_date),
            "accounting_period_end": str(end_date),
            "turnover": str(gross_income.quantize(Decimal("0.01"))),
            "total_allowable_expenses": str(total_expenses.quantize(Decimal("0.01"))),
            "net_profit_or_loss": str(net_profit.quantize(Decimal("0.01"))),
            "income_breakdown": [
                {"category_id": row.category_id, "total": str(Decimal(str(row.total)).quantize(Decimal("0.01")))}
                for row in income_rows
            ],
            "expense_breakdown": [
                {"category_id": row.category_id, "total": str(Decimal(str(row.total)).quantize(Decimal("0.01")))}
                for row in expense_rows
            ],
        },
        "tax_calculation": {
            "income_tax": str(income_tax.quantize(Decimal("0.01"))),
            "class_2_ni": str(ni_class2.quantize(Decimal("0.01"))),
            "class_4_ni": str(ni_class4.quantize(Decimal("0.01"))),
            "total_tax_due": str((income_tax + ni_class2 + ni_class4).quantize(Decimal("0.01"))),
        },
    }

    # Save to TaxYear record
    tax_year_record = (
        db.query(TaxYear)
        .filter(TaxYear.tenant_id == TENANT_ID, TaxYear.year_label == tax_year)
        .first()
    )
    if tax_year_record is not None:
        tax_year_record.sa_data = sa_data
        db.commit()
    else:
        new_record = TaxYear(
            tenant_id=TENANT_ID,
            year_label=tax_year,
            start_date=start_date,
            end_date=end_date,
            sa_data=sa_data,
        )
        db.add(new_record)
        db.commit()

    return sa_data
