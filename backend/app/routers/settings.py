from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Setting, Entity, Category, CategoryType
from app.schemas import (
    SettingCreate, SettingResponse, EntityCreate, EntityResponse,
    CategoryCreate, CategoryResponse,
)

router = APIRouter(prefix="/settings", tags=["settings"])

TENANT_ID = 1


# ---- General Settings ----

@router.get("", response_model=list[SettingResponse])
def list_settings(db: Session = Depends(get_db)):
    return (
        db.query(Setting)
        .filter(Setting.tenant_id == TENANT_ID)
        .order_by(Setting.key)
        .all()
    )


@router.get("/{key}", response_model=SettingResponse)
def get_setting(key: str, db: Session = Depends(get_db)):
    setting = (
        db.query(Setting)
        .filter(Setting.tenant_id == TENANT_ID, Setting.key == key)
        .first()
    )
    if setting is None:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    return setting


@router.put("/{key}", response_model=SettingResponse)
def upsert_setting(key: str, data: SettingCreate, db: Session = Depends(get_db)):
    setting = (
        db.query(Setting)
        .filter(Setting.tenant_id == TENANT_ID, Setting.key == key)
        .first()
    )

    if setting is not None:
        setting.value = data.value
    else:
        setting = Setting(
            tenant_id=TENANT_ID,
            key=key,
            value=data.value,
        )
        db.add(setting)

    db.commit()
    db.refresh(setting)
    return setting


@router.delete("/{key}", status_code=204)
def delete_setting(key: str, db: Session = Depends(get_db)):
    setting = (
        db.query(Setting)
        .filter(Setting.tenant_id == TENANT_ID, Setting.key == key)
        .first()
    )
    if setting is None:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")
    db.delete(setting)
    db.commit()
    return None


# ---- Entity Settings ----

@router.get("/entity/list", response_model=list[EntityResponse])
def list_entities(db: Session = Depends(get_db)):
    return (
        db.query(Entity)
        .filter(Entity.tenant_id == TENANT_ID)
        .all()
    )


@router.get("/entity/{entity_id}", response_model=EntityResponse)
def get_entity(entity_id: int, db: Session = Depends(get_db)):
    entity = (
        db.query(Entity)
        .filter(Entity.id == entity_id, Entity.tenant_id == TENANT_ID)
        .first()
    )
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.post("/entity", response_model=EntityResponse, status_code=201)
def create_entity(data: EntityCreate, db: Session = Depends(get_db)):
    entity = Entity(
        tenant_id=TENANT_ID,
        entity_type=data.entity_type,
        business_name=data.business_name,
        address=data.address,
        utr_number=data.utr_number,
        company_number=data.company_number,
        vat_number=data.vat_number,
        base_currency=data.base_currency,
        tax_year_start=data.tax_year_start,
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


@router.put("/entity/{entity_id}", response_model=EntityResponse)
def update_entity(
    entity_id: int, data: EntityCreate, db: Session = Depends(get_db)
):
    entity = (
        db.query(Entity)
        .filter(Entity.id == entity_id, Entity.tenant_id == TENANT_ID)
        .first()
    )
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")

    entity.entity_type = data.entity_type
    entity.business_name = data.business_name
    entity.address = data.address
    entity.utr_number = data.utr_number
    entity.company_number = data.company_number
    entity.vat_number = data.vat_number
    entity.base_currency = data.base_currency
    entity.tax_year_start = data.tax_year_start

    db.commit()
    db.refresh(entity)
    return entity


# ---- Categories ----

@router.get("/categories/list", response_model=list[CategoryResponse])
def list_categories(
    type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Category).filter(Category.tenant_id == TENANT_ID)
    if type is not None:
        query = query.filter(Category.type == type)
    return query.order_by(Category.type, Category.name).all()


@router.get("/categories/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    cat = (
        db.query(Category)
        .filter(Category.id == category_id, Category.tenant_id == TENANT_ID)
        .first()
    )
    if cat is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.post("/categories", response_model=CategoryResponse, status_code=201)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    cat = Category(
        tenant_id=TENANT_ID,
        name=data.name,
        type=data.type,
        is_default=data.is_default,
        hmrc_code=data.hmrc_code,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int, data: CategoryCreate, db: Session = Depends(get_db)
):
    cat = (
        db.query(Category)
        .filter(Category.id == category_id, Category.tenant_id == TENANT_ID)
        .first()
    )
    if cat is None:
        raise HTTPException(status_code=404, detail="Category not found")

    cat.name = data.name
    cat.type = data.type
    cat.is_default = data.is_default
    cat.hmrc_code = data.hmrc_code

    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/categories/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = (
        db.query(Category)
        .filter(Category.id == category_id, Category.tenant_id == TENANT_ID)
        .first()
    )
    if cat is None:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()
    return None


# ---- HMRC Knowledge Base ----

@router.get("/hmrc/expense-categories")
def hmrc_expense_categories():
    """Return HMRC-standard expense categories with descriptions for reference."""
    return {
        "categories": [
            {
                "hmrc_code": "cost_of_goods",
                "name": "Cost of goods bought for resale or goods used",
                "description": "Stock, raw materials, direct costs of goods sold.",
            },
            {
                "hmrc_code": "wages",
                "name": "Wages, salaries and other staff costs",
                "description": "Employee wages, salaries, bonuses, employer NI contributions.",
            },
            {
                "hmrc_code": "car_van",
                "name": "Car, van and travel expenses",
                "description": "Vehicle running costs, fuel, parking, public transport, business mileage.",
            },
            {
                "hmrc_code": "rent",
                "name": "Rent, rates, power and insurance costs",
                "description": "Business premises rent, business rates, utilities, insurance.",
            },
            {
                "hmrc_code": "repairs",
                "name": "Repairs and maintenance of property and equipment",
                "description": "Repairs to business premises, equipment maintenance.",
            },
            {
                "hmrc_code": "phone_internet",
                "name": "Phone, fax, stationery and other office costs",
                "description": "Phone bills, internet, stationery, postage, office supplies.",
            },
            {
                "hmrc_code": "advertising",
                "name": "Advertising and business entertainment costs",
                "description": "Marketing, advertising, website costs. Note: business entertainment is not allowable.",
            },
            {
                "hmrc_code": "interest",
                "name": "Interest on bank and other loans",
                "description": "Interest on business loans, overdraft interest.",
            },
            {
                "hmrc_code": "bank_charges",
                "name": "Bank, credit card and other financial charges",
                "description": "Bank charges, credit card fees, payment processing fees.",
            },
            {
                "hmrc_code": "irrecoverable",
                "name": "Irrecoverable debts written off",
                "description": "Bad debts that cannot be recovered.",
            },
            {
                "hmrc_code": "accountancy",
                "name": "Accountancy, legal and other professional fees",
                "description": "Accountant fees, legal fees, professional subscriptions.",
            },
            {
                "hmrc_code": "depreciation",
                "name": "Depreciation and loss/profit on sale of assets",
                "description": "Not allowable for tax - use capital allowances instead.",
            },
            {
                "hmrc_code": "other",
                "name": "Other business expenses",
                "description": "Any other allowable business expenses not covered above.",
            },
            {
                "hmrc_code": "use_of_home",
                "name": "Use of home as office",
                "description": "Proportion of home costs used for business (simplified: flat rate based on hours worked).",
            },
        ],
        "notes": [
            "These categories align with HMRC SA103 (Self Employment) supplementary pages.",
            "Capital allowances are claimed separately from revenue expenses.",
            "Business entertainment costs are generally not allowable.",
            "Mixed-use expenses should be apportioned to the business element only.",
        ],
    }


# ---- AI Config ----

@router.get("/ai/config")
def get_ai_config(db: Session = Depends(get_db)):
    """Get current AI configuration settings."""
    ai_keys = ["ai_enabled", "ai_auto_categorise", "ai_receipt_scanning", "ai_monthly_summary"]
    settings_list = (
        db.query(Setting)
        .filter(Setting.tenant_id == TENANT_ID, Setting.key.in_(ai_keys))
        .all()
    )
    config = {s.key: s.value for s in settings_list}

    return {
        "ai_enabled": config.get("ai_enabled", "false"),
        "ai_auto_categorise": config.get("ai_auto_categorise", "true"),
        "ai_receipt_scanning": config.get("ai_receipt_scanning", "true"),
        "ai_monthly_summary": config.get("ai_monthly_summary", "true"),
    }


# ---- Invoice Settings ----

@router.get("/invoice/config")
def get_invoice_config(db: Session = Depends(get_db)):
    """Get invoice configuration (default payment terms, numbering, etc.)."""
    inv_keys = [
        "invoice_prefix", "invoice_next_number", "invoice_default_payment_terms",
        "invoice_default_notes", "invoice_bank_details",
    ]
    settings_list = (
        db.query(Setting)
        .filter(Setting.tenant_id == TENANT_ID, Setting.key.in_(inv_keys))
        .all()
    )
    config = {s.key: s.value for s in settings_list}

    return {
        "invoice_prefix": config.get("invoice_prefix", "INV-"),
        "invoice_next_number": config.get("invoice_next_number", "1"),
        "invoice_default_payment_terms": config.get("invoice_default_payment_terms", "30 days"),
        "invoice_default_notes": config.get("invoice_default_notes", ""),
        "invoice_bank_details": config.get("invoice_bank_details", ""),
    }
