from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


# ---------- Tenant ----------
class TenantCreate(BaseModel):
    name: str


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    created_at: datetime


# ---------- Entity ----------
class EntityCreate(BaseModel):
    entity_type: str = "sole_trader"
    business_name: str
    address: Optional[str] = None
    utr_number: Optional[str] = None
    company_number: Optional[str] = None
    vat_number: Optional[str] = None
    base_currency: str = "GBP"
    tax_year_start: Optional[date] = None


class EntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    entity_type: str
    business_name: str
    address: Optional[str] = None
    utr_number: Optional[str] = None
    company_number: Optional[str] = None
    vat_number: Optional[str] = None
    base_currency: str
    tax_year_start: Optional[date] = None
    created_at: datetime
    updated_at: datetime


# ---------- Category ----------
class CategoryCreate(BaseModel):
    name: str
    type: str  # income or expense
    is_default: bool = False
    hmrc_code: Optional[str] = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    name: str
    type: str
    is_default: bool
    hmrc_code: Optional[str] = None
    created_at: datetime


# ---------- Transaction ----------
class TransactionCreate(BaseModel):
    type: str  # income or expense
    date: date
    description: str
    source: str = "manual"
    original_amount: Decimal
    currency: str = "GBP"
    exchange_rate: Decimal = Decimal("1.0")
    gbp_amount: Optional[Decimal] = None
    category_id: Optional[int] = None
    notes: Optional[str] = None
    receipt_file_path: Optional[str] = None
    allowable_percentage: Decimal = Decimal("100")
    import_profile_id: Optional[int] = None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    type: str
    date: date
    description: str
    source: str
    original_amount: Decimal
    currency: str
    exchange_rate: Decimal
    gbp_amount: Decimal
    category_id: Optional[int] = None
    notes: Optional[str] = None
    receipt_file_path: Optional[str] = None
    allowable_percentage: Decimal
    import_profile_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool


class TransactionFilter(BaseModel):
    type: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    category_id: Optional[int] = None
    source: Optional[str] = None
    search: Optional[str] = None
    include_deleted: bool = False


# ---------- Invoice ----------
class InvoiceLineItem(BaseModel):
    description: str
    quantity: Decimal = Decimal("1")
    unit_price: Decimal
    amount: Decimal


class InvoiceCreate(BaseModel):
    invoice_number: str
    status: str = "draft"
    client_name: str
    client_address: Optional[str] = None
    client_email: Optional[str] = None
    line_items: list[InvoiceLineItem] = []
    subtotal: Decimal
    tax_amount: Decimal = Decimal("0")
    total: Decimal
    currency: str = "GBP"
    payment_terms: Optional[str] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None
    linked_transaction_id: Optional[int] = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    invoice_number: str
    status: str
    client_name: str
    client_address: Optional[str] = None
    client_email: Optional[str] = None
    line_items: list = []
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    currency: str
    payment_terms: Optional[str] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None
    pdf_file_path: Optional[str] = None
    linked_transaction_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class InvoiceStatusUpdate(BaseModel):
    status: str


# ---------- Incoming Invoice ----------
class IncomingInvoiceCreate(BaseModel):
    supplier_name: str
    invoice_number: Optional[str] = None
    date: date
    due_date: Optional[date] = None
    line_items: Optional[list] = None
    total: Decimal
    currency: str = "GBP"
    file_path: Optional[str] = None
    linked_transaction_id: Optional[int] = None


class IncomingInvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    supplier_name: str
    invoice_number: Optional[str] = None
    date: date
    due_date: Optional[date] = None
    line_items: Optional[list] = None
    total: Decimal
    currency: str
    file_path: Optional[str] = None
    linked_transaction_id: Optional[int] = None
    created_at: datetime


# ---------- PAYE ----------
class PAYEEntryCreate(BaseModel):
    month: int = Field(ge=1, le=12)
    tax_year: str
    gross_pay: Decimal
    tax_deducted: Decimal
    ni_deducted: Decimal
    student_loan: Decimal = Decimal("0")
    other_deductions: Decimal = Decimal("0")
    notes: Optional[str] = None


class PAYEEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    month: int
    tax_year: str
    gross_pay: Decimal
    tax_deducted: Decimal
    ni_deducted: Decimal
    student_loan: Decimal
    other_deductions: Decimal
    notes: Optional[str] = None
    created_at: datetime


class PAYESummary(BaseModel):
    tax_year: str
    total_gross_pay: Decimal
    total_tax_deducted: Decimal
    total_ni_deducted: Decimal
    total_student_loan: Decimal
    total_other_deductions: Decimal
    net_pay: Decimal
    months_recorded: int


# ---------- Import Profile ----------
class ImportProfileCreate(BaseModel):
    name: str
    column_mappings: dict = {}
    skip_rows: int = 0
    date_format: str = "%Y-%m-%d"
    target_type: str  # income or expense


class ImportProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    name: str
    column_mappings: dict
    skip_rows: int
    date_format: str
    target_type: str
    created_at: datetime
    updated_at: datetime


# ---------- Tax ----------
class TaxSummary(BaseModel):
    tax_year: str
    gross_income: Decimal
    total_expenses: Decimal
    taxable_profit: Decimal
    personal_allowance: Decimal
    income_tax: Decimal
    ni_class2: Decimal
    ni_class4: Decimal
    total_tax: Decimal
    effective_rate: Decimal
    income_tax_breakdown: list[dict] = []


# ---------- Reports ----------
class PnLReport(BaseModel):
    period_start: date
    period_end: date
    total_income: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    income_by_category: list[dict] = []
    expenses_by_category: list[dict] = []


class ExpenseBreakdown(BaseModel):
    period_start: date
    period_end: date
    total: Decimal
    categories: list[dict] = []


class IncomeBySource(BaseModel):
    period_start: date
    period_end: date
    total: Decimal
    sources: list[dict] = []


class CashflowEntry(BaseModel):
    month: str
    income: Decimal
    expenses: Decimal
    net: Decimal


class CashflowReport(BaseModel):
    period_start: date
    period_end: date
    months: list[CashflowEntry] = []
    total_income: Decimal
    total_expenses: Decimal
    total_net: Decimal


# ---------- AI / Scanning ----------
class ReceiptScanResult(BaseModel):
    vendor: str
    date: Optional[date] = None
    total: Optional[Decimal] = None
    currency: str = "GBP"
    description: Optional[str] = None
    suggested_category: Optional[str] = None
    confidence: float = 0.0
    line_items: list[dict] = []


class InvoiceScanResult(BaseModel):
    supplier_name: Optional[str] = None
    invoice_number: Optional[str] = None
    date: Optional[date] = None
    due_date: Optional[date] = None
    total: Optional[Decimal] = None
    currency: str = "GBP"
    line_items: list[dict] = []
    confidence: float = 0.0


class CategorySuggestion(BaseModel):
    transaction_description: str
    suggested_category_id: Optional[int] = None
    suggested_category_name: str
    confidence: float = 0.0
    reasoning: str = ""


class MonthlySummaryAI(BaseModel):
    month: str
    summary: str
    highlights: list[str] = []
    concerns: list[str] = []
    suggestions: list[str] = []


class ImportAnalysisResult(BaseModel):
    detected_columns: list[dict] = []
    suggested_mappings: dict = {}
    sample_rows: list[dict] = []
    suggested_date_format: str = "%Y-%m-%d"
    row_count: int = 0


# ---------- Settings ----------
class SettingCreate(BaseModel):
    key: str
    value: str


class SettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    tenant_id: int
    key: str
    value: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ---------- Exchange Rate ----------
class ExchangeRateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    currency: str
    date: date
    rate_to_gbp: Decimal
    source: str


# ---------- Paginated Response ----------
class PaginatedResponse(BaseModel):
    items: list = []
    total: int
    page: int
    page_size: int
    pages: int
