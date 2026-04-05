# Seedling Tax — Full Application Specification
 
## Overview
 
Seedling Tax is a bookkeeping and tax management application for UK sole traders and small limited companies. It tracks income, expenses, generates and stores invoices, handles multi-currency transactions, and prepares HMRC Self Assessment data. An AI layer (Claude API) assists with receipt scanning, invoice reading, data import profiling, categorisation, and tax insights.
 
The application is built for a single user initially but must be **multi-tenant ready** from day one (PostgreSQL with row-level tenant isolation, same pattern as Seedling Ledger).
 
---
 
## Tech Stack
 
- **Frontend**: React (Vite)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL with row-level tenant isolation
- **Email**: Resend (transactional email for invoice delivery)
- **AI**: Claude API (configurable model names — see Settings)
- **Currency**: Frankfurter API (https://api.frankfurter.dev/v2/rates)
- **Auth**: FastAPI auth (same pattern as Seedling VPS auth server)
- **Payments** (future): Stripe subscriptions when SaaS-ready
 
---
 
## Design System — "DOS Modern"
 
The UI has a unique hybrid aesthetic: DOS-era keyboard-first navigation with modern, clean form inputs. This is NOT a typical SaaS look.
 
### Philosophy
- **Keyboard-first**: Every action has a hotkey. Tab/Shift-Tab navigates form fields. Number keys select sidebar items. Alt+letter selects menu items.
- **Inverse highlight bar**: The selected/active menu item or sidebar item uses an inverse color scheme (light background, dark text) — like a DOS-era cursor bar.
- **Modern forms**: Input fields are clean, Google Forms-style with generous padding, clear labels, and a prominent focus state (coloured border + subtle glow on the active field).
 
### Colour Palette
- **Main background**: `#7A7A78` (calming medium warm grey)
- **Dark elements** (topbar, statusbar): `#2C2C2A`
- **Panel/sidebar background**: `#8E8E8B` with `rgba(0,0,0,0.12)` overlay for sidebar
- **Light text**: `#F1EFE8`
- **Dimmed text**: `#B4B2A9`
- **Accent (teal/green)**: `#5DCAA5` (highlights, active states, positive values)
- **Accent dark**: `#0F6E56` (buttons, badges)
- **Warning/expense**: `#EF9F27` / `#FAC775`
- **Input background**: `#F1EFE8`
- **Input border (default)**: `#B4B2A9`
- **Input focus border**: `#5DCAA5` with `box-shadow: 0 0 0 3px rgba(93,202,165,0.2)`
- **Inverse highlight**: background `#F1EFE8`, text `#2C2C2A`
 
### Typography
- **Monospace** (menus, navigation, statusbar, labels): `IBM Plex Mono` (400, 500)
- **Sans-serif** (form inputs, body text, reports): `IBM Plex Sans` (400, 500)
 
### Layout Structure
```
┌─────────────────────────────────────────────────┐
│ TOPBAR: logo left, context info right           │  (#2C2C2A)
├─────────────────────────────────────────────────┤
│ MENU BAR: horizontal items with hotkey letters  │  (#8E8E8B)
├────────┬────────────────────────────────────────┤
│SIDEBAR │  MAIN CONTENT AREA                     │
│ items  │  (forms, tables, charts, summaries)    │
│ with   │                                        │
│ number │  Input fields are compact and properly  │
│ keys   │  sized to their context — small fields  │
│        │  for dates/amounts, wider for text.     │
│        │  Panels with lots of data use compact   │
│        │  tables and dense layouts.              │
├────────┴────────────────────────────────────────┤
│ STATUSBAR: hotkey hints left, app info right     │  (#2C2C2A)
└─────────────────────────────────────────────────┘
```
 
### Menu Items (with hotkeys)
**D**ashboard · **I**ncome · **E**xpenses · In**v**oices · **T**ax · **R**eports · **S**ettings
 
### Component Guidelines
- **Summary cards**: dark translucent background `rgba(0,0,0,0.15)`, 4px border-radius, 3px coloured left border (teal for income, amber for expenses, default for neutral). Label: 10px uppercase mono. Value: 18px/500 mono.
- **Tables**: compact rows, monospace for numbers, sans-serif for descriptions. Alternating subtle row backgrounds.
- **Buttons**: Primary = accent-dark bg with accent text. Secondary = translucent white bg with dim text. Always show hotkey in parentheses: "Save (Enter)", "Cancel (Esc)".
- **Sidebar items**: show hotkey number/combo right-aligned. Active item gets inverse highlight.
- **Statusbar**: always visible, shows context-relevant hotkeys on the left, app version/info on the right.
 
### Critical UX Rules
- **Every interactive element must be reachable by keyboard.**
- **Tab order must be logical** — forms flow top-to-bottom, left-to-right.
- **Active/focused elements are always visually obvious** — inverse bar for navigation, coloured border for inputs.
- **Input field sizes must be proportional to their content** — don't make a date field as wide as a description field. Use grid layouts with appropriate column ratios.
 
---
 
## Entity Mode
 
The application supports two entity types, switchable in Settings:
 
### Sole Trader Mode (default)
- Income reported as self-employment income
- Expenses claimed as allowable business expenses
- Tax calculated as Income Tax + Class 2/4 NI
- Invoices show personal name
- Self Assessment: SA100 + SA103 (self-employment supplement)
 
### Limited Company (LTD) Mode
- Income is company revenue
- Corporation Tax applies
- Director's salary vs dividends tracking
- Invoices show company name + company number + VAT number (if VAT registered)
- Payment terms field on invoices (e.g. "Net 30")
- VAT threshold monitoring
 
Switching mode does NOT delete data — it changes how data is categorised and taxed. All historical transactions remain and can be re-viewed under either mode.
 
---
 
## Modules
 
### 1. Dashboard
 
**Sidebar items**: Overview (1), Recent activity (2), Monthly summary (3), Agent insights (4)
 
**Quick actions in sidebar**: Quick add... (N), Import data... (Ctrl+I), Scan receipt... (Ctrl+R)
 
**Overview panel**:
- Summary cards: Income YTD, Expenses YTD, Estimated Tax Owed
- Recent transactions list (last 10)
- Current month mini P&L
- Alerts/warnings from the AI agent (approaching VAT threshold, uncategorised items, unpaid invoices, etc.)
 
### 2. Income
 
Track all business income from multiple sources.
 
**Income types**:
- **Self-employment income**: manual entry or imported from Stripe/apps
- **PAYE income**: monthly payslip entry (gross pay, tax deducted, NI contributions, student loan if applicable). This builds a cumulative PAYE picture throughout the year. At year end, the P60 can be entered for verification/reconciliation.
 
**Fields per income entry**:
- Date, Description, Source (dropdown: manual, Stripe, Seedling VPS, Seedling Ledger, Camplas, PAYE, Other)
- Amount, Currency (GBP/EUR/USD/HUF/other)
- If non-GBP: auto-fetch exchange rate from Frankfurter API for that date, store original amount + currency + rate + GBP equivalent
- Category, Notes, Attached receipt/proof (file upload)
 
**Import functionality** (see Import Module below)
 
### 3. Expenses
 
Track all allowable business expenses.
 
**Fields per expense entry**:
- Date, Description, Supplier/Vendor
- Amount, Currency (same multi-currency logic as income)
- Category (HMRC-aligned categories — see below)
- Receipt attachment (image/PDF)
- Allowable percentage (default 100%, adjustable for mixed-use expenses like phone bills)
- Notes
 
**HMRC Expense Categories** (configurable in Settings):
- Office/premises costs
- Travel costs
- Clothing expenses (uniforms only)
- Staff costs
- Stock/materials
- Financial costs (bank charges, interest)
- IT & hosting (domains, servers, SaaS subscriptions)
- Software & subscriptions
- Marketing & advertising
- Professional services (accountant, legal)
- Phone, internet (allowable portion)
- Training & development
- Insurance
- Other allowable expenses
 
**Receipt Scanning**:
- Upload photo or PDF of a receipt
- AI (Claude Vision API, using the "fast model") analyses the image
- Pre-fills: date, vendor/merchant, amount, currency, suggested category
- User reviews and confirms/edits before saving
- Original receipt file stored permanently alongside the expense record
 
### 4. Invoices
 
Two-directional invoice management.
 
#### Outgoing Invoices (generated by user)
- Create invoice with: client name, client address, line items (description, quantity, unit price, tax), payment terms, due date, notes
- Auto-assign sequential invoice number (configurable prefix, e.g. "SW-2026-001")
- **Generate PDF** and store permanently in the system — the stored PDF is the canonical version
- **Send via email** (Resend API) with PDF attachment
- **Re-send / download** the exact same stored PDF at any time (no regeneration — the original file is served)
- Track payment status: Draft → Sent → Paid / Overdue
- When paid, link to corresponding income entry
- In LTD mode: invoice shows company name, company number, VAT number, payment terms
 
#### Incoming Invoices (received from suppliers)
- Upload PDF or photo
- AI scans and pre-fills: supplier, invoice number, date, due date, line items, total, currency
- User reviews/edits, confirms
- Links to expense entry
- Original file stored permanently
 
### 5. Tax
 
**PAYE Tracking**:
- Monthly payslip entries accumulate throughout the year
- Shows running totals: gross pay, tax paid, NI paid
- Year-end P60 entry for reconciliation
 
**Self-Employment Tax Calculation**:
- Total self-employment income minus allowable expenses = taxable profit
- Apply Income Tax bands (use current year rates from HMRC knowledge base)
- Apply Class 2 NI (flat rate if above threshold)
- Apply Class 4 NI (percentage bands)
- Show: gross income, total expenses, taxable profit, income tax, NI, total tax liability, effective tax rate
 
**Self Assessment Preparation**:
- Generate data needed for SA100 + SA103 forms
- Categorised summary of all income and expenses in HMRC-required format
- Export as PDF report that can be used to fill in the online Self Assessment
- AI (smart model) reviews the data and flags potential issues, missing information, or optimisation opportunities
 
**LTD Mode Tax**:
- Corporation Tax calculation
- Director's salary tracking
- Dividend tracking and dividend tax calculation
- VAT tracking if VAT registered
 
**HMRC Exchange Rates**:
- Ability to download HMRC official monthly exchange rates for the full tax year
- "Recalculate with HMRC rates" function that re-computes all foreign currency transactions using HMRC monthly rates instead of the daily Frankfurter rates
- Store both versions — user chooses which to use for the Self Assessment
 
### 6. Reports
 
All reports support date range filtering (custom, monthly, quarterly, yearly, tax year) and export to CSV and PDF.
 
**Available Reports**:
- **Profit & Loss (P&L)**: income vs expenses breakdown, monthly/quarterly/yearly
- **Expense Breakdown**: by category, by time period, with percentage of total
- **Income by Source**: which app/client/source generates what revenue
- **Tax Overview**: gross income, allowable expenses, taxable profit, estimated tax, effective tax rate, pre-tax vs post-tax comparison
- **Monthly Trend Charts**: income vs expenses bar chart over time
- **Category Distribution**: pie/donut charts for expense categories and income sources
- **Cash Flow**: net income over time
- **Product/Service Breakdown**: if tracking by product (e.g. Seedling VPS, Ledger, Camplas)
- **VAT Report** (if applicable): VAT collected vs VAT paid
 
**Charts**: Use Recharts (React) for all data visualisation. Line charts for trends, bar charts for comparisons, pie/donut for breakdowns.
 
### 7. Settings
 
**General**: Business name, address, entity type (sole trader / LTD), tax year, base currency (GBP), UTR number, company number (LTD), VAT number (if registered)
 
**AI Configuration**:
- "Fast model" — used for receipt scanning, categorisation, import profiling. Default: `claude-haiku-4-5-20251001`. User can change the model string.
- "Smart model" — used for tax analysis, monthly summaries, Self Assessment preparation, HMRC rule interpretation. Default: `claude-sonnet-4-6`. User can change the model string.
- API key configuration for Claude API
 
**HMRC Knowledge Base**: A stored, condensed version of current UK tax rules that the AI uses as context. Editable/updatable by the user. Covers: Income Tax bands, NI thresholds/rates, allowable expense rules, Self Assessment deadlines, VAT threshold, mileage allowances, etc.
 
**Import Profiles**: Manage saved import configurations (see Import Module)
 
**Expense Categories**: Add/edit/remove expense categories
 
**Invoice Settings**: Invoice number prefix, default payment terms, business logo (for PDF invoices), bank details (for invoices)
 
---
 
## Import Module (AI-Taught Profiles)
 
This is a key feature. When the user uploads a CSV or Excel file for import:
 
1. User uploads file and gives it a name (e.g. "Stripe", "Hetzner", "Seedling VPS")
2. AI (fast model) analyses the file structure:
   - Identifies column headers and data types
   - Determines which columns map to: date, description, amount, currency, category, reference number, etc.
   - Identifies where the actual data starts (skip header rows) and ends
   - Handles different date formats
3. AI presents the mapping to the user for confirmation/adjustment
4. User confirms → mapping saved as an "Import Profile"
5. Next time the user uploads a file with the same profile name, the mapping is applied automatically
6. Imported rows become income or expense entries (as configured in the profile)
 
Import profiles are stored in the database and editable in Settings.
 
---
 
## Multi-Currency
 
- All transactions store: original amount, original currency, exchange rate, GBP equivalent
- Exchange rates fetched from Frankfurter API: `https://api.frankfurter.dev/v2/rates?base={CURRENCY}&quotes=GBP&date={DATE}`
- Rates cached in the database (one fetch per currency per date)
- Supported currencies: all 160+ from Frankfurter (GBP, EUR, USD, HUF prominently shown, others searchable)
- HMRC monthly official rates can be downloaded and stored separately
- "Recalculate with HMRC rates" function available in Tax module
 
---
 
## AI Integration
 
All AI features use the Claude API with user-configurable model names.
 
### Fast Model (default: Haiku)
- **Receipt scanning**: Vision API — extract merchant, date, amount, currency, category from receipt photos/PDFs
- **Invoice scanning**: Vision API — extract supplier, invoice number, date, line items, totals from incoming invoice PDFs/images
- **Category suggestion**: Based on description and historical categorisation patterns (context-learning with last 20 similar transactions as few-shot examples, same pattern as Seedling Ledger)
- **Import profile creation**: Analyse CSV/Excel structure and suggest column mappings
 
### Smart Model (default: Sonnet)
- **Monthly summary**: End-of-month summary of income, expenses, notable changes, actionable insights
- **Tax optimisation suggestions**: Based on current data, suggest ways to optimise tax position (e.g. "You have £X in uncategorised expenses that may be allowable")
- **Self Assessment preparation**: Review all data, flag issues, generate SA-ready summary
- **HMRC rule interpretation**: Answer questions about tax rules using the knowledge base as context
- **Anomaly detection**: Flag unusual transactions, potential duplicate entries, missing receipts
 
### Context Learning Pattern
Same as Seedling Ledger: when categorising or scanning, include up to 20 previous similar records as few-shot examples in the prompt. This teaches the AI the user's specific patterns without fine-tuning.
 
---
 
## Database Schema (Key Tables)
 
```
entities          — business entity settings (sole_trader / ltd), one per tenant
transactions      — all income and expense records
  - type: income | expense
  - original_amount, currency, exchange_rate, gbp_amount
  - category_id, description, date, notes
  - receipt_file_path
  - source (manual, import, scan)
  - import_profile_id (if imported)
categories        — expense/income categories (HMRC-aligned defaults + custom)
invoices          — outgoing invoices
  - status: draft | sent | paid | overdue
  - pdf_file_path (stored PDF)
  - client details, line items (JSON or separate table)
incoming_invoices — received invoices
  - linked expense transaction
  - original file path
paye_entries      — monthly payslip data
  - gross_pay, tax_deducted, ni_deducted, student_loan, other_deductions
  - month, tax_year
import_profiles   — saved import configurations
  - name, column_mappings (JSON), skip_rows, date_format, etc.
exchange_rates    — cached daily rates from Frankfurter
hmrc_rates        — HMRC official monthly rates
tax_years         — tax year configurations and SA data
tenants           — multi-tenant support
users             — user accounts (tenant-linked)
```
 
---
 
## File Storage
 
- **Receipts**: uploaded receipt images/PDFs stored on disk, path in database
- **Invoice PDFs**: generated once and stored permanently, path in database. Never regenerated — the stored file is the canonical version. Can be re-sent or re-downloaded.
- **Incoming invoice files**: stored on disk, path in database
- **Storage path**: `/opt/seedling-tax-data/files/{tenant_id}/{type}/{year}/{filename}`
 
---
 
## API Endpoints (Key Routes)
 
```
# Transactions
POST   /api/transactions          — create income or expense
GET    /api/transactions          — list with filters (type, date range, category, source)
PUT    /api/transactions/{id}     — update
DELETE /api/transactions/{id}     — soft delete
 
# AI
POST   /api/ai/scan-receipt       — upload image/PDF, returns pre-filled fields
POST   /api/ai/scan-invoice       — upload incoming invoice, returns pre-filled fields
POST   /api/ai/categorise         — suggest category for a transaction
POST   /api/ai/monthly-summary    — generate monthly summary
POST   /api/ai/import-analyse     — analyse uploaded file, suggest column mappings
 
# Invoices
POST   /api/invoices              — create outgoing invoice
GET    /api/invoices/{id}/pdf     — download stored PDF
POST   /api/invoices/{id}/send    — send invoice via email
PATCH  /api/invoices/{id}/status  — update payment status
 
# Import
POST   /api/import/upload         — upload CSV/Excel with profile name
GET    /api/import/profiles       — list import profiles
PUT    /api/import/profiles/{id}  — edit import profile
 
# PAYE
POST   /api/paye                  — add monthly payslip entry
GET    /api/paye/summary          — PAYE year-to-date summary
 
# Tax
GET    /api/tax/summary           — current tax year calculation
POST   /api/tax/hmrc-rates        — download HMRC rates for tax year
POST   /api/tax/recalculate       — recalculate with HMRC rates
GET    /api/tax/self-assessment    — generate SA data export
 
# Reports
GET    /api/reports/pnl           — profit & loss
GET    /api/reports/expenses      — expense breakdown
GET    /api/reports/income        — income by source
GET    /api/reports/tax           — tax overview
GET    /api/reports/cashflow      — cash flow over time
 
# Currency
GET    /api/currency/rate         — get rate for currency+date (fetches from Frankfurter if not cached)
 
# Settings
GET/PUT /api/settings/entity      — entity configuration
GET/PUT /api/settings/ai          — AI model configuration
GET/PUT /api/settings/invoice     — invoice defaults
GET/PUT /api/settings/categories  — manage categories
GET/PUT /api/settings/knowledge   — HMRC knowledge base content
```
 
---
 
## UK Tax Year
 
The UK tax year runs **6 April to 5 April**. The application defaults to this. All YTD calculations, reports, and Self Assessment data are based on the tax year, not calendar year.
 
Self Assessment deadlines:
- Paper return: 31 October following end of tax year
- Online return: 31 January following end of tax year
- Payment deadline: 31 January (with possible payments on account 31 July)
 
---
 
## Notes for Implementation
 
- Start with the core: transactions (income/expenses), dashboard, and the DOS Modern UI shell with full keyboard navigation.
- Add AI features incrementally — receipt scanning first, then categorisation, then import profiles.
- Invoice generation can come next, followed by tax calculations and reports.
- The HMRC knowledge base should be seeded with current 2026/27 tax year data (tax bands, NI rates, thresholds). This needs to be scraped or manually compiled from HMRC's website.
- The mockup HTML file (provided separately) defines the design language — colours, fonts, component styles, layout structure. Input sizes and layouts should be adapted to each panel's content density.
- Remember: this is a Seedling Works product. It follows the same deployment and infrastructure patterns as Seedling VPS and Seedling Ledger.
