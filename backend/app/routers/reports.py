from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from app.database import get_db
from app.models import Transaction, TransactionType, Category, CategoryType
from app.schemas import PnLReport, ExpenseBreakdown, IncomeBySource, CashflowReport, CashflowEntry

router = APIRouter(prefix="/reports", tags=["reports"])

TENANT_ID = 1


def _default_date_range() -> tuple[date, date]:
    """Default to current UK tax year."""
    today = date.today()
    if today.month >= 4 and today.day >= 6:
        start = date(today.year, 4, 6)
    else:
        start = date(today.year - 1, 4, 6)
    end = date(start.year + 1, 4, 5)
    return start, end


@router.get("/pnl", response_model=PnLReport)
def profit_and_loss(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    if date_from is None or date_to is None:
        date_from, date_to = _default_date_range()

    base_filter = [
        Transaction.tenant_id == TENANT_ID,
        Transaction.is_deleted == False,
        Transaction.date >= date_from,
        Transaction.date <= date_to,
    ]

    # Income by category
    income_cats = (
        db.query(
            Category.name,
            func.coalesce(func.sum(
                Transaction.gbp_amount * Transaction.allowable_percentage / 100
            ), 0).label("total"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .filter(*base_filter, Transaction.type == TransactionType.income)
        .group_by(Category.name)
        .all()
    )

    # Expense by category
    expense_cats = (
        db.query(
            Category.name,
            func.coalesce(func.sum(
                Transaction.gbp_amount * Transaction.allowable_percentage / 100
            ), 0).label("total"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .filter(*base_filter, Transaction.type == TransactionType.expense)
        .group_by(Category.name)
        .all()
    )

    income_by_cat = [
        {"category": row.name or "Uncategorised", "total": str(Decimal(str(row.total)).quantize(Decimal("0.01")))}
        for row in income_cats
    ]
    expenses_by_cat = [
        {"category": row.name or "Uncategorised", "total": str(Decimal(str(row.total)).quantize(Decimal("0.01")))}
        for row in expense_cats
    ]

    total_income = sum(Decimal(r["total"]) for r in income_by_cat)
    total_expenses = sum(Decimal(r["total"]) for r in expenses_by_cat)

    return PnLReport(
        period_start=date_from,
        period_end=date_to,
        total_income=total_income,
        total_expenses=total_expenses,
        net_profit=total_income - total_expenses,
        income_by_category=income_by_cat,
        expenses_by_category=expenses_by_cat,
    )


@router.get("/expenses", response_model=ExpenseBreakdown)
def expense_breakdown(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    if date_from is None or date_to is None:
        date_from, date_to = _default_date_range()

    rows = (
        db.query(
            Category.name,
            Category.hmrc_code,
            func.coalesce(func.sum(
                Transaction.gbp_amount * Transaction.allowable_percentage / 100
            ), 0).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .filter(
            Transaction.tenant_id == TENANT_ID,
            Transaction.is_deleted == False,
            Transaction.type == TransactionType.expense,
            Transaction.date >= date_from,
            Transaction.date <= date_to,
        )
        .group_by(Category.name, Category.hmrc_code)
        .order_by(func.sum(Transaction.gbp_amount).desc())
        .all()
    )

    categories = [
        {
            "category": row.name or "Uncategorised",
            "hmrc_code": row.hmrc_code,
            "total": str(Decimal(str(row.total)).quantize(Decimal("0.01"))),
            "count": row.count,
        }
        for row in rows
    ]

    total = sum(Decimal(c["total"]) for c in categories)

    return ExpenseBreakdown(
        period_start=date_from,
        period_end=date_to,
        total=total,
        categories=categories,
    )


@router.get("/income-by-source", response_model=IncomeBySource)
def income_by_source(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    if date_from is None or date_to is None:
        date_from, date_to = _default_date_range()

    rows = (
        db.query(
            Transaction.source,
            func.coalesce(func.sum(
                Transaction.gbp_amount * Transaction.allowable_percentage / 100
            ), 0).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .filter(
            Transaction.tenant_id == TENANT_ID,
            Transaction.is_deleted == False,
            Transaction.type == TransactionType.income,
            Transaction.date >= date_from,
            Transaction.date <= date_to,
        )
        .group_by(Transaction.source)
        .order_by(func.sum(Transaction.gbp_amount).desc())
        .all()
    )

    sources = [
        {
            "source": str(row.source.value) if hasattr(row.source, "value") else str(row.source),
            "total": str(Decimal(str(row.total)).quantize(Decimal("0.01"))),
            "count": row.count,
        }
        for row in rows
    ]

    total = sum(Decimal(s["total"]) for s in sources)

    return IncomeBySource(
        period_start=date_from,
        period_end=date_to,
        total=total,
        sources=sources,
    )


@router.get("/tax-overview")
def tax_overview(
    tax_year: str = "2026/27",
    db: Session = Depends(get_db),
):
    """Quick tax overview combining P&L and tax estimates."""
    parts = tax_year.split("/")
    start_year = int(parts[0])
    start_date = date(start_year, 4, 6)
    end_date = date(start_year + 1, 4, 5)

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

    income_count = (
        db.query(func.count(Transaction.id))
        .filter(
            Transaction.tenant_id == TENANT_ID,
            Transaction.type == TransactionType.income,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.is_deleted == False,
        )
        .scalar()
    )

    expense_count = (
        db.query(func.count(Transaction.id))
        .filter(
            Transaction.tenant_id == TENANT_ID,
            Transaction.type == TransactionType.expense,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.is_deleted == False,
        )
        .scalar()
    )

    gross_income = Decimal(str(income_result)).quantize(Decimal("0.01"))
    total_expenses = Decimal(str(expense_result)).quantize(Decimal("0.01"))
    net_profit = gross_income - total_expenses

    return {
        "tax_year": tax_year,
        "gross_income": str(gross_income),
        "total_expenses": str(total_expenses),
        "net_profit": str(net_profit),
        "income_transactions": income_count,
        "expense_transactions": expense_count,
        "period_start": str(start_date),
        "period_end": str(end_date),
    }


@router.get("/cashflow", response_model=CashflowReport)
def cashflow_report(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
):
    if date_from is None or date_to is None:
        date_from, date_to = _default_date_range()

    # Get monthly income
    income_monthly = (
        db.query(
            extract("year", Transaction.date).label("year"),
            extract("month", Transaction.date).label("month"),
            func.coalesce(func.sum(Transaction.gbp_amount), 0).label("total"),
        )
        .filter(
            Transaction.tenant_id == TENANT_ID,
            Transaction.type == TransactionType.income,
            Transaction.is_deleted == False,
            Transaction.date >= date_from,
            Transaction.date <= date_to,
        )
        .group_by("year", "month")
        .all()
    )

    # Get monthly expenses
    expense_monthly = (
        db.query(
            extract("year", Transaction.date).label("year"),
            extract("month", Transaction.date).label("month"),
            func.coalesce(func.sum(Transaction.gbp_amount), 0).label("total"),
        )
        .filter(
            Transaction.tenant_id == TENANT_ID,
            Transaction.type == TransactionType.expense,
            Transaction.is_deleted == False,
            Transaction.date >= date_from,
            Transaction.date <= date_to,
        )
        .group_by("year", "month")
        .all()
    )

    income_map: dict[str, Decimal] = {}
    for row in income_monthly:
        key = f"{int(row.year)}-{int(row.month):02d}"
        income_map[key] = Decimal(str(row.total))

    expense_map: dict[str, Decimal] = {}
    for row in expense_monthly:
        key = f"{int(row.year)}-{int(row.month):02d}"
        expense_map[key] = Decimal(str(row.total))

    all_months = sorted(set(list(income_map.keys()) + list(expense_map.keys())))

    months = []
    total_income = Decimal("0")
    total_expenses = Decimal("0")

    for month_key in all_months:
        inc = income_map.get(month_key, Decimal("0"))
        exp = expense_map.get(month_key, Decimal("0"))
        net = inc - exp
        total_income += inc
        total_expenses += exp
        months.append(CashflowEntry(
            month=month_key,
            income=inc.quantize(Decimal("0.01")),
            expenses=exp.quantize(Decimal("0.01")),
            net=net.quantize(Decimal("0.01")),
        ))

    return CashflowReport(
        period_start=date_from,
        period_end=date_to,
        months=months,
        total_income=total_income.quantize(Decimal("0.01")),
        total_expenses=total_expenses.quantize(Decimal("0.01")),
        total_net=(total_income - total_expenses).quantize(Decimal("0.01")),
    )
