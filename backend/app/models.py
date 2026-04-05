from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date, Text, JSON,
    ForeignKey, Index, Numeric, Enum as SAEnum
)
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class EntityType(str, enum.Enum):
    sole_trader = "sole_trader"
    ltd = "ltd"


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class TransactionSource(str, enum.Enum):
    manual = "manual"
    stripe = "stripe"
    seedling_vps = "seedling_vps"
    seedling_ledger = "seedling_ledger"
    camplas = "camplas"
    paye = "paye"
    other = "other"
    import_ = "import"


class CategoryType(str, enum.Enum):
    income = "income"
    expense = "expense"


class InvoiceStatus(str, enum.Enum):
    draft = "draft"
    sent = "sent"
    paid = "paid"
    overdue = "overdue"


class ExchangeRateSource(str, enum.Enum):
    frankfurter = "frankfurter"
    hmrc = "hmrc"


class ImportTargetType(str, enum.Enum):
    income = "income"
    expense = "expense"


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    users = relationship("User", back_populates="tenant")
    entities = relationship("Entity", back_populates="tenant")
    categories = relationship("Category", back_populates="tenant")
    transactions = relationship("Transaction", back_populates="tenant")
    invoices = relationship("Invoice", back_populates="tenant")
    incoming_invoices = relationship("IncomingInvoice", back_populates="tenant")
    paye_entries = relationship("PAYEEntry", back_populates="tenant")
    import_profiles = relationship("ImportProfile", back_populates="tenant")
    tax_years = relationship("TaxYear", back_populates="tenant")
    settings = relationship("Setting", back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="users")


class Entity(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    entity_type = Column(SAEnum(EntityType), nullable=False, default=EntityType.sole_trader)
    business_name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    utr_number = Column(String(20), nullable=True)
    company_number = Column(String(20), nullable=True)
    vat_number = Column(String(20), nullable=True)
    base_currency = Column(String(3), default="GBP", nullable=False)
    tax_year_start = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="entities")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(SAEnum(CategoryType), nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    hmrc_code = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    transactions = relationship("Transaction", back_populates="category")
    tenant = relationship("Tenant", back_populates="categories")

    __table_args__ = (
        Index("ix_categories_tenant_type", "tenant_id", "type"),
    )


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    type = Column(SAEnum(TransactionType), nullable=False)
    date = Column(Date, nullable=False, index=True)
    description = Column(String(500), nullable=False)
    source = Column(SAEnum(TransactionSource), default=TransactionSource.manual, nullable=False)
    original_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="GBP", nullable=False)
    exchange_rate = Column(Numeric(12, 6), default=1.0, nullable=False)
    gbp_amount = Column(Numeric(12, 2), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    notes = Column(Text, nullable=True)
    receipt_file_path = Column(String(500), nullable=True)
    allowable_percentage = Column(Numeric(5, 2), default=100, nullable=False)
    import_profile_id = Column(Integer, ForeignKey("import_profiles.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    category = relationship("Category", back_populates="transactions")
    tenant = relationship("Tenant", back_populates="transactions")
    import_profile = relationship("ImportProfile", back_populates="transactions")

    __table_args__ = (
        Index("ix_transactions_tenant_date", "tenant_id", "date"),
        Index("ix_transactions_tenant_type", "tenant_id", "type"),
        Index("ix_transactions_tenant_source", "tenant_id", "source"),
        Index("ix_transactions_tenant_deleted", "tenant_id", "is_deleted"),
    )


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    invoice_number = Column(String(50), nullable=False)
    status = Column(SAEnum(InvoiceStatus), default=InvoiceStatus.draft, nullable=False)
    client_name = Column(String(255), nullable=False)
    client_address = Column(Text, nullable=True)
    client_email = Column(String(255), nullable=True)
    line_items = Column(JSON, nullable=False, default=list)
    subtotal = Column(Numeric(12, 2), nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0, nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="GBP", nullable=False)
    payment_terms = Column(String(255), nullable=True)
    due_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    pdf_file_path = Column(String(500), nullable=True)
    linked_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    linked_transaction = relationship("Transaction", foreign_keys=[linked_transaction_id])
    tenant = relationship("Tenant", back_populates="invoices")

    __table_args__ = (
        Index("ix_invoices_tenant_status", "tenant_id", "status"),
    )


class IncomingInvoice(Base):
    __tablename__ = "incoming_invoices"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_name = Column(String(255), nullable=False)
    invoice_number = Column(String(50), nullable=True)
    date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)
    line_items = Column(JSON, nullable=True, default=list)
    total = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="GBP", nullable=False)
    file_path = Column(String(500), nullable=True)
    linked_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    linked_transaction = relationship("Transaction", foreign_keys=[linked_transaction_id])
    tenant = relationship("Tenant", back_populates="incoming_invoices")


class PAYEEntry(Base):
    __tablename__ = "paye_entries"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    month = Column(Integer, nullable=False)
    tax_year = Column(String(10), nullable=False)
    gross_pay = Column(Numeric(12, 2), nullable=False)
    tax_deducted = Column(Numeric(12, 2), nullable=False)
    ni_deducted = Column(Numeric(12, 2), nullable=False)
    student_loan = Column(Numeric(12, 2), default=0, nullable=False)
    other_deductions = Column(Numeric(12, 2), default=0, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="paye_entries")

    __table_args__ = (
        Index("ix_paye_entries_tenant_year", "tenant_id", "tax_year"),
    )


class ImportProfile(Base):
    __tablename__ = "import_profiles"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    column_mappings = Column(JSON, nullable=False, default=dict)
    skip_rows = Column(Integer, default=0, nullable=False)
    date_format = Column(String(50), default="%Y-%m-%d", nullable=False)
    target_type = Column(SAEnum(ImportTargetType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    transactions = relationship("Transaction", back_populates="import_profile")
    tenant = relationship("Tenant", back_populates="import_profiles")


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True, index=True)
    currency = Column(String(3), nullable=False)
    date = Column(Date, nullable=False)
    rate_to_gbp = Column(Numeric(12, 6), nullable=False)
    source = Column(SAEnum(ExchangeRateSource), default=ExchangeRateSource.frankfurter, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_exchange_rates_currency_date", "currency", "date", unique=True),
    )


class HMRCRate(Base):
    __tablename__ = "hmrc_rates"

    id = Column(Integer, primary_key=True, index=True)
    currency = Column(String(3), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    rate_to_gbp = Column(Numeric(12, 6), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_hmrc_rates_currency_period", "currency", "year", "month", unique=True),
    )


class TaxYear(Base):
    __tablename__ = "tax_years"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    year_label = Column(String(10), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    sa_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="tax_years")

    __table_args__ = (
        Index("ix_tax_years_tenant_label", "tenant_id", "year_label", unique=True),
    )


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    key = Column(String(255), nullable=False)
    value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="settings")

    __table_args__ = (
        Index("ix_settings_tenant_key", "tenant_id", "key", unique=True),
    )
