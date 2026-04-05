from contextlib import asynccontextmanager
from datetime import date, datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal, Base
from app.models import (
    Tenant, Entity, Category, CategoryType, EntityType,
)
from app.routers import transactions, invoices, paye, tax, reports, currency, settings, ai, imports


DEFAULT_EXPENSE_CATEGORIES = [
    ("Cost of goods bought for resale or goods used", "cost_of_goods"),
    ("Wages, salaries and other staff costs", "wages"),
    ("Car, van and travel expenses", "car_van"),
    ("Rent, rates, power and insurance costs", "rent"),
    ("Repairs and maintenance of property and equipment", "repairs"),
    ("Phone, fax, stationery and other office costs", "phone_internet"),
    ("Advertising and business entertainment costs", "advertising"),
    ("Interest on bank and other loans", "interest"),
    ("Bank, credit card and other financial charges", "bank_charges"),
    ("Irrecoverable debts written off", "irrecoverable"),
    ("Accountancy, legal and other professional fees", "accountancy"),
    ("Depreciation and loss/profit on sale of assets", "depreciation"),
    ("Other business expenses", "other"),
    ("Use of home as office", "use_of_home"),
]

DEFAULT_INCOME_CATEGORIES = [
    ("Self-employment income", None),
    ("PAYE income", None),
    ("Client payment", None),
    ("Other", None),
]


def seed_default_data(db: Session) -> None:
    """Create default tenant, categories, and entity if they don't exist."""
    # Default tenant
    tenant = db.query(Tenant).filter(Tenant.id == 1).first()
    if tenant is None:
        tenant = Tenant(id=1, name="Default Tenant")
        db.add(tenant)
        db.flush()

    # Default expense categories
    existing_categories = (
        db.query(Category)
        .filter(Category.tenant_id == 1, Category.is_default == True)
        .count()
    )

    if existing_categories == 0:
        for name, hmrc_code in DEFAULT_EXPENSE_CATEGORIES:
            cat = Category(
                tenant_id=1,
                name=name,
                type=CategoryType.expense,
                is_default=True,
                hmrc_code=hmrc_code,
            )
            db.add(cat)

        for name, hmrc_code in DEFAULT_INCOME_CATEGORIES:
            cat = Category(
                tenant_id=1,
                name=name,
                type=CategoryType.income,
                is_default=True,
                hmrc_code=hmrc_code,
            )
            db.add(cat)

    # Default entity
    existing_entity = (
        db.query(Entity)
        .filter(Entity.tenant_id == 1)
        .first()
    )
    if existing_entity is None:
        entity = Entity(
            tenant_id=1,
            entity_type=EntityType.sole_trader,
            business_name="My Business",
            base_currency="GBP",
            tax_year_start=date(2026, 4, 6),
        )
        db.add(entity)

    db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed data
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_default_data(db)
    finally:
        db.close()
    yield
    # Shutdown: nothing to clean up


app = FastAPI(
    title="Seedling Tax",
    description="Bookkeeping and tax management API for UK sole traders and small limited companies",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers under /api prefix
app.include_router(transactions.router, prefix="/api")
app.include_router(invoices.router, prefix="/api")
app.include_router(paye.router, prefix="/api")
app.include_router(tax.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(currency.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(imports.router, prefix="/api")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "seedling-tax-api",
        "version": "0.1.0",
    }


@app.get("/")
def root():
    return {
        "name": "Seedling Tax API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
