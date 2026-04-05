from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.database import get_db
from app.models import Transaction, TransactionType, TransactionSource
from app.schemas import (
    TransactionCreate, TransactionResponse, PaginatedResponse
)

router = APIRouter(prefix="/transactions", tags=["transactions"])

TENANT_ID = 1


@router.get("", response_model=PaginatedResponse)
def list_transactions(
    type: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category_id: Optional[int] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    include_deleted: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Transaction).filter(Transaction.tenant_id == TENANT_ID)

    if not include_deleted:
        query = query.filter(Transaction.is_deleted == False)

    if type is not None:
        query = query.filter(Transaction.type == type)

    if date_from is not None:
        query = query.filter(Transaction.date >= date_from)

    if date_to is not None:
        query = query.filter(Transaction.date <= date_to)

    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)

    if source is not None:
        query = query.filter(Transaction.source == source)

    if search is not None and search.strip():
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Transaction.description.ilike(search_term),
                Transaction.notes.ilike(search_term),
            )
        )

    total = query.count()
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    transactions = (
        query.order_by(Transaction.date.desc(), Transaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        items=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    txn = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.tenant_id == TENANT_ID,
        )
        .first()
    )
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn


@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(data: TransactionCreate, db: Session = Depends(get_db)):
    gbp_amount = data.gbp_amount
    if gbp_amount is None:
        gbp_amount = data.original_amount * data.exchange_rate

    txn = Transaction(
        tenant_id=TENANT_ID,
        type=data.type,
        date=data.date,
        description=data.description,
        source=data.source,
        original_amount=data.original_amount,
        currency=data.currency,
        exchange_rate=data.exchange_rate,
        gbp_amount=gbp_amount,
        category_id=data.category_id,
        notes=data.notes,
        receipt_file_path=data.receipt_file_path,
        allowable_percentage=data.allowable_percentage,
        import_profile_id=data.import_profile_id,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


@router.put("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: int,
    data: TransactionCreate,
    db: Session = Depends(get_db),
):
    txn = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.tenant_id == TENANT_ID,
            Transaction.is_deleted == False,
        )
        .first()
    )
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    gbp_amount = data.gbp_amount
    if gbp_amount is None:
        gbp_amount = data.original_amount * data.exchange_rate

    txn.type = data.type
    txn.date = data.date
    txn.description = data.description
    txn.source = data.source
    txn.original_amount = data.original_amount
    txn.currency = data.currency
    txn.exchange_rate = data.exchange_rate
    txn.gbp_amount = gbp_amount
    txn.category_id = data.category_id
    txn.notes = data.notes
    txn.receipt_file_path = data.receipt_file_path
    txn.allowable_percentage = data.allowable_percentage
    txn.import_profile_id = data.import_profile_id

    db.commit()
    db.refresh(txn)
    return txn


@router.delete("/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    txn = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.tenant_id == TENANT_ID,
        )
        .first()
    )
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    txn.is_deleted = True
    db.commit()
    return None


@router.post("/{transaction_id}/restore", response_model=TransactionResponse)
def restore_transaction(transaction_id: int, db: Session = Depends(get_db)):
    txn = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.tenant_id == TENANT_ID,
            Transaction.is_deleted == True,
        )
        .first()
    )
    if txn is None:
        raise HTTPException(status_code=404, detail="Deleted transaction not found")

    txn.is_deleted = False
    db.commit()
    db.refresh(txn)
    return txn
