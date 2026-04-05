import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import DataTable from '../components/DataTable';
import FormInput from '../components/FormInput';
import Modal from '../components/Modal';
import SummaryCard from '../components/SummaryCard';
import useKeyboard from '../hooks/useKeyboard';
import { getTransactions, createTransaction, getPAYEEntries, createPAYEEntry } from '../api/client';

const SIDEBAR_ITEMS = [
  { key: 'all', label: 'All income', shortcut: '1' },
  { key: 'self-employment', label: 'Self-employment', shortcut: '2' },
  { key: 'paye', label: 'PAYE', shortcut: '3' },
  { key: 'by-source', label: 'By source', shortcut: '4' },
  { divider: true },
  { key: 'add', label: 'Add income...', shortcut: 'N' },
  { key: 'import', label: 'Import...', shortcut: 'Ctrl+I' },
];

const STATUS_HINTS = [
  { key: 'Alt+I', label: 'Income' },
  { key: '1-4', label: 'Navigate' },
  { key: 'N', label: 'Add income' },
  { key: '?', label: 'Shortcuts' },
];

const INCOME_COLUMNS = [
  { key: 'date', label: 'Date', type: 'date', width: '100px' },
  { key: 'description', label: 'Description' },
  { key: 'source', label: 'Source', width: '130px' },
  { key: 'amount', label: 'Amount', type: 'currency', width: '110px' },
  { key: 'category', label: 'Category', width: '130px' },
];

const PAYE_COLUMNS = [
  { key: 'month', label: 'Month', width: '120px' },
  { key: 'gross_pay', label: 'Gross Pay', type: 'currency', width: '110px' },
  { key: 'tax_deducted', label: 'Tax', type: 'currency', width: '100px' },
  { key: 'ni_deducted', label: 'NI', type: 'currency', width: '100px' },
  { key: 'student_loan', label: 'Student Loan', type: 'currency', width: '110px' },
  { key: 'net_pay', label: 'Net Pay', type: 'currency', width: '110px' },
];

const SOURCE_OPTIONS = [
  'Self-employment',
  'PAYE employment',
  'Freelance',
  'Rental',
  'Dividends',
  'Interest',
  'Other',
];

const DEFAULT_INCOME = {
  date: new Date().toISOString().slice(0, 10),
  description: '',
  source: '',
  amount: '',
  currency: 'GBP',
  category: '',
  notes: '',
};

const DEFAULT_PAYE = {
  month: '',
  gross_pay: '',
  tax_deducted: '',
  ni_deducted: '',
  student_loan: '',
};

const MONTHS = [
  'April', 'May', 'June', 'July', 'August', 'September',
  'October', 'November', 'December', 'January', 'February', 'March',
];

export default function Income({ activeModule, onModuleChange }) {
  const [activePanel, setActivePanel] = useState('all');
  const [incomeData, setIncomeData] = useState([]);
  const [payeEntries, setPayeEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [form, setForm] = useState({ ...DEFAULT_INCOME });
  const [payeForm, setPayeForm] = useState({ ...DEFAULT_PAYE });

  const handleSidebarChange = useCallback((key) => {
    if (key === 'add') {
      setShowAddModal(true);
      return;
    }
    setActivePanel(key);
  }, []);

  useKeyboard({
    onNumberKey: (num) => {
      const item = SIDEBAR_ITEMS.filter((i) => !i.divider)[num - 1];
      if (item) handleSidebarChange(item.key);
    },
    onEscape: () => setShowAddModal(false),
  });

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [txData, payeData] = await Promise.all([
          getTransactions({ type: 'income' }),
          getPAYEEntries(),
        ]);
        if (!cancelled) {
          setIncomeData(Array.isArray(txData) ? txData : []);
          setPayeEntries(Array.isArray(payeData) ? payeData : []);
        }
      } catch {
        if (!cancelled) {
          setIncomeData([]);
          setPayeEntries([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const updateForm = (field) => (val) => setForm((prev) => ({ ...prev, [field]: val }));
  const updatePayeForm = (field) => (val) => setPayeForm((prev) => ({ ...prev, [field]: val }));

  const handleAddIncome = async () => {
    if (!form.description || !form.amount) return;
    try {
      const tx = await createTransaction({
        ...form,
        type: 'income',
        amount: parseFloat(form.amount),
      });
      setIncomeData((prev) => [tx, ...prev]);
    } catch {
      // API unavailable
    }
    setForm({ ...DEFAULT_INCOME });
    setShowAddModal(false);
  };

  const handleAddPaye = async () => {
    if (!payeForm.month || !payeForm.gross_pay) return;
    const entry = {
      ...payeForm,
      gross_pay: parseFloat(payeForm.gross_pay) || 0,
      tax_deducted: parseFloat(payeForm.tax_deducted) || 0,
      ni_deducted: parseFloat(payeForm.ni_deducted) || 0,
      student_loan: parseFloat(payeForm.student_loan) || 0,
      net_pay:
        (parseFloat(payeForm.gross_pay) || 0) -
        (parseFloat(payeForm.tax_deducted) || 0) -
        (parseFloat(payeForm.ni_deducted) || 0) -
        (parseFloat(payeForm.student_loan) || 0),
    };
    try {
      const saved = await createPAYEEntry(entry);
      setPayeEntries((prev) => [...prev, saved]);
    } catch {
      setPayeEntries((prev) => [...prev, { ...entry, id: Date.now() }]);
    }
    setPayeForm({ ...DEFAULT_PAYE });
  };

  const selfEmploymentData = incomeData.filter(
    (t) => t.source === 'Self-employment' || t.source === 'Freelance'
  );

  const bySource = incomeData.reduce((acc, t) => {
    const src = t.source || 'Uncategorised';
    if (!acc[src]) acc[src] = [];
    acc[src].push(t);
    return acc;
  }, {});

  const totalIncome = incomeData.reduce((s, t) => s + (parseFloat(t.amount) || 0), 0);

  const payeTotals = payeEntries.reduce(
    (acc, e) => ({
      gross_pay: acc.gross_pay + (parseFloat(e.gross_pay) || 0),
      tax_deducted: acc.tax_deducted + (parseFloat(e.tax_deducted) || 0),
      ni_deducted: acc.ni_deducted + (parseFloat(e.ni_deducted) || 0),
      student_loan: acc.student_loan + (parseFloat(e.student_loan) || 0),
      net_pay: acc.net_pay + (parseFloat(e.net_pay) || 0),
    }),
    { gross_pay: 0, tax_deducted: 0, ni_deducted: 0, student_loan: 0, net_pay: 0 }
  );

  const fmt = (n) => `\u00a3${n.toLocaleString('en-GB', { minimumFractionDigits: 2 })}`;

  const renderAll = () => (
    <>
      <div className="section-title">All income</div>
      <div className="summary-cards">
        <SummaryCard label="Total Income YTD" value={fmt(totalIncome)} variant="good" />
        <SummaryCard label="Transactions" value={String(incomeData.length)} variant="neutral" />
      </div>
      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <DataTable
          columns={INCOME_COLUMNS}
          data={incomeData}
          emptyMessage="No income recorded yet. Press N to add."
        />
      )}
    </>
  );

  const renderSelfEmployment = () => (
    <>
      <div className="section-title">Self-employment income</div>
      <DataTable
        columns={INCOME_COLUMNS}
        data={selfEmploymentData}
        emptyMessage="No self-employment income recorded"
      />
    </>
  );

  const renderPaye = () => (
    <>
      <div className="section-title">PAYE entries</div>
      <div className="panel-box">
        <div className="section-subtitle">Add payslip</div>
        <div className="form-row">
          <FormInput label="Month" type="select" value={payeForm.month} onChange={updatePayeForm('month')} options={MONTHS} placeholder="Select month" size="medium" />
          <FormInput label="Gross pay" type="number" value={payeForm.gross_pay} onChange={updatePayeForm('gross_pay')} placeholder="0.00" step="0.01" size="small" />
          <FormInput label="Tax deducted" type="number" value={payeForm.tax_deducted} onChange={updatePayeForm('tax_deducted')} placeholder="0.00" step="0.01" size="small" />
        </div>
        <div className="form-row" style={{ marginTop: 12 }}>
          <FormInput label="NI deducted" type="number" value={payeForm.ni_deducted} onChange={updatePayeForm('ni_deducted')} placeholder="0.00" step="0.01" size="small" />
          <FormInput label="Student loan" type="number" value={payeForm.student_loan} onChange={updatePayeForm('student_loan')} placeholder="0.00" step="0.01" size="small" />
        </div>
        <div className="form-actions">
          <button className="btn btn-primary" onClick={handleAddPaye}>Add entry</button>
        </div>
      </div>

      <div className="section-subtitle" style={{ marginTop: 16 }}>Running totals</div>
      <DataTable
        columns={PAYE_COLUMNS}
        data={payeEntries}
        emptyMessage="No PAYE entries yet"
      />
      {payeEntries.length > 0 && (
        <div className="summary-cards" style={{ marginTop: 16 }}>
          <SummaryCard label="Gross Total" value={fmt(payeTotals.gross_pay)} variant="neutral" />
          <SummaryCard label="Tax Paid" value={fmt(payeTotals.tax_deducted)} variant="warn" />
          <SummaryCard label="NI Paid" value={fmt(payeTotals.ni_deducted)} variant="warn" />
          <SummaryCard label="Net Total" value={fmt(payeTotals.net_pay)} variant="good" />
        </div>
      )}
    </>
  );

  const renderBySource = () => (
    <>
      <div className="section-title">Income by source</div>
      {Object.keys(bySource).length === 0 ? (
        <div className="empty-state">No income data to group</div>
      ) : (
        Object.entries(bySource).map(([source, items]) => {
          const total = items.reduce((s, t) => s + (parseFloat(t.amount) || 0), 0);
          return (
            <div key={source}>
              <div className="group-header">{source}</div>
              <DataTable columns={INCOME_COLUMNS} data={items} />
              <div className="group-total">Total: {fmt(total)}</div>
            </div>
          );
        })
      )}
    </>
  );

  const panels = { all: renderAll, 'self-employment': renderSelfEmployment, paye: renderPaye, 'by-source': renderBySource };

  return (
    <Layout
      activeModule={activeModule}
      onModuleChange={onModuleChange}
      sidebarItems={SIDEBAR_ITEMS}
      activeSidebarItem={activePanel}
      onSidebarChange={handleSidebarChange}
      statusHints={STATUS_HINTS}
    >
      {(panels[activePanel] || renderAll)()}

      <Modal isOpen={showAddModal} onClose={() => setShowAddModal(false)} title="Add Income">
        <div className="form-row">
          <FormInput label="Date" type="date" value={form.date} onChange={updateForm('date')} size="small" />
          <FormInput label="Source" type="select" value={form.source} onChange={updateForm('source')} options={SOURCE_OPTIONS} placeholder="Select source" size="medium" />
        </div>
        <div style={{ marginTop: 12 }}>
          <FormInput label="Description" type="text" value={form.description} onChange={updateForm('description')} placeholder="Invoice payment, salary, etc." />
        </div>
        <div className="form-row" style={{ marginTop: 12 }}>
          <FormInput label="Amount" type="number" value={form.amount} onChange={updateForm('amount')} placeholder="0.00" step="0.01" size="small" />
          <FormInput label="Currency" type="select" value={form.currency} onChange={updateForm('currency')} options={['GBP', 'USD', 'EUR']} size="small" />
          <FormInput label="Category" type="text" value={form.category} onChange={updateForm('category')} placeholder="e.g. Consulting" size="medium" />
        </div>
        <div style={{ marginTop: 12 }}>
          <FormInput label="Notes" type="textarea" value={form.notes} onChange={updateForm('notes')} placeholder="Optional notes..." />
        </div>
        <div className="modal-footer" style={{ padding: '12px 0 0', borderTop: 'none' }}>
          <button className="btn btn-ghost" onClick={() => setShowAddModal(false)}>Cancel</button>
          <button className="btn btn-primary" onClick={handleAddIncome}>Save income</button>
        </div>
      </Modal>
    </Layout>
  );
}
