from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Invoice, IncomingInvoice
from app.schemas import (
    InvoiceCreate, InvoiceResponse, InvoiceStatusUpdate,
    IncomingInvoiceCreate, IncomingInvoiceResponse,
    PaginatedResponse,
)

router = APIRouter(prefix="/invoices", tags=["invoices"])

TENANT_ID = 1


# ---- Outgoing Invoices ----

@router.get("", response_model=PaginatedResponse)
def list_invoices(
    status: Optional[str] = None,
    client_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(Invoice).filter(Invoice.tenant_id == TENANT_ID)

    if status is not None:
        query = query.filter(Invoice.status == status)
    if client_name is not None:
        query = query.filter(Invoice.client_name.ilike(f"%{client_name}%"))

    total = query.count()
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    invoices = (
        query.order_by(Invoice.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        items=[InvoiceResponse.model_validate(i) for i in invoices],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.tenant_id == TENANT_ID)
        .first()
    )
    if inv is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return inv


@router.post("", response_model=InvoiceResponse, status_code=201)
def create_invoice(data: InvoiceCreate, db: Session = Depends(get_db)):
    line_items_dicts = [item.model_dump() for item in data.line_items]
    inv = Invoice(
        tenant_id=TENANT_ID,
        invoice_number=data.invoice_number,
        status=data.status,
        client_name=data.client_name,
        client_address=data.client_address,
        client_email=data.client_email,
        line_items=line_items_dicts,
        subtotal=data.subtotal,
        tax_amount=data.tax_amount,
        total=data.total,
        currency=data.currency,
        payment_terms=data.payment_terms,
        due_date=data.due_date,
        notes=data.notes,
        linked_transaction_id=data.linked_transaction_id,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@router.put("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: int, data: InvoiceCreate, db: Session = Depends(get_db)
):
    inv = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.tenant_id == TENANT_ID)
        .first()
    )
    if inv is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    line_items_dicts = [item.model_dump() for item in data.line_items]
    inv.invoice_number = data.invoice_number
    inv.status = data.status
    inv.client_name = data.client_name
    inv.client_address = data.client_address
    inv.client_email = data.client_email
    inv.line_items = line_items_dicts
    inv.subtotal = data.subtotal
    inv.tax_amount = data.tax_amount
    inv.total = data.total
    inv.currency = data.currency
    inv.payment_terms = data.payment_terms
    inv.due_date = data.due_date
    inv.notes = data.notes
    inv.linked_transaction_id = data.linked_transaction_id

    db.commit()
    db.refresh(inv)
    return inv


@router.patch("/{invoice_id}/status", response_model=InvoiceResponse)
def update_invoice_status(
    invoice_id: int, data: InvoiceStatusUpdate, db: Session = Depends(get_db)
):
    inv = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.tenant_id == TENANT_ID)
        .first()
    )
    if inv is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    valid_statuses = {"draft", "sent", "paid", "overdue"}
    if data.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}",
        )

    inv.status = data.status
    db.commit()
    db.refresh(inv)
    return inv


@router.delete("/{invoice_id}", status_code=204)
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.tenant_id == TENANT_ID)
        .first()
    )
    if inv is None:
        raise HTTPException(status_code=404, detail="Invoice not found")
    db.delete(inv)
    db.commit()
    return None


@router.get("/{invoice_id}/pdf")
def get_invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    inv = (
        db.query(Invoice)
        .filter(Invoice.id == invoice_id, Invoice.tenant_id == TENANT_ID)
        .first()
    )
    if inv is None:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return {
        "message": "PDF generation placeholder",
        "invoice_id": inv.id,
        "invoice_number": inv.invoice_number,
        "status": "PDF generation will be implemented with ReportLab",
    }


# ---- Incoming Invoices ----

@router.get("/incoming/", response_model=PaginatedResponse)
def list_incoming_invoices(
    supplier_name: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(IncomingInvoice).filter(
        IncomingInvoice.tenant_id == TENANT_ID
    )

    if supplier_name is not None:
        query = query.filter(
            IncomingInvoice.supplier_name.ilike(f"%{supplier_name}%")
        )

    total = query.count()
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    items = (
        query.order_by(IncomingInvoice.date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        items=[IncomingInvoiceResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/incoming/{invoice_id}", response_model=IncomingInvoiceResponse)
def get_incoming_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = (
        db.query(IncomingInvoice)
        .filter(
            IncomingInvoice.id == invoice_id,
            IncomingInvoice.tenant_id == TENANT_ID,
        )
        .first()
    )
    if inv is None:
        raise HTTPException(status_code=404, detail="Incoming invoice not found")
    return inv


@router.post("/incoming/", response_model=IncomingInvoiceResponse, status_code=201)
def create_incoming_invoice(
    data: IncomingInvoiceCreate, db: Session = Depends(get_db)
):
    inv = IncomingInvoice(
        tenant_id=TENANT_ID,
        supplier_name=data.supplier_name,
        invoice_number=data.invoice_number,
        date=data.date,
        due_date=data.due_date,
        line_items=data.line_items,
        total=data.total,
        currency=data.currency,
        file_path=data.file_path,
        linked_transaction_id=data.linked_transaction_id,
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@router.put("/incoming/{invoice_id}", response_model=IncomingInvoiceResponse)
def update_incoming_invoice(
    invoice_id: int,
    data: IncomingInvoiceCreate,
    db: Session = Depends(get_db),
):
    inv = (
        db.query(IncomingInvoice)
        .filter(
            IncomingInvoice.id == invoice_id,
            IncomingInvoice.tenant_id == TENANT_ID,
        )
        .first()
    )
    if inv is None:
        raise HTTPException(status_code=404, detail="Incoming invoice not found")

    inv.supplier_name = data.supplier_name
    inv.invoice_number = data.invoice_number
    inv.date = data.date
    inv.due_date = data.due_date
    inv.line_items = data.line_items
    inv.total = data.total
    inv.currency = data.currency
    inv.file_path = data.file_path
    inv.linked_transaction_id = data.linked_transaction_id

    db.commit()
    db.refresh(inv)
    return inv


@router.delete("/incoming/{invoice_id}", status_code=204)
def delete_incoming_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = (
        db.query(IncomingInvoice)
        .filter(
            IncomingInvoice.id == invoice_id,
            IncomingInvoice.tenant_id == TENANT_ID,
        )
        .first()
    )
    if inv is None:
        raise HTTPException(status_code=404, detail="Incoming invoice not found")
    db.delete(inv)
    db.commit()
    return None
