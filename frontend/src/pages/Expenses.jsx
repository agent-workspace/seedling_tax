import React, { useState, useEffect, useCallback, useRef } from 'react';
import Layout from '../components/Layout';
import DataTable from '../components/DataTable';
import FormInput from '../components/FormInput';
import Modal from '../components/Modal';
import SummaryCard from '../components/SummaryCard';
import useKeyboard from '../hooks/useKeyboard';
import { getTransactions, createTransaction, scanReceipt } from '../api/client';

const SIDEBAR_ITEMS = [
  { key: 'all', label: 'All expenses', shortcut: '1' },
  { key: 'by-category', label: 'By category', shortcut: '2' },
  { key: 'receipts', label: 'Receipts', shortcut: '3' },
  { divider: true },
  { key: 'add', label: 'Add expense...', shortcut: 'N' },
  { key: 'scan', label: 'Scan receipt...', shortcut: 'Ctrl+R' },
];

const STATUS_HINTS = [
  { key: 'Alt+E', label: 'Expenses' },
  { key: '1-3', label: 'Navigate' },
  { key: 'N', label: 'Add expense' },
  { key: '?', label: 'Shortcuts' },
];

const EXPENSE_COLUMNS = [
  { key: 'date', label: 'Date', type: 'date', width: '100px' },
  { key: 'description', label: 'Description' },
  { key: 'supplier', label: 'Supplier', width: '130px' },
  { key: 'amount', label: 'Amount', type: 'currency', width: '110px' },
  { key: 'category', label: 'Category', width: '140px' },
  { key: 'has_receipt', label: 'Receipt', type: 'receipt', width: '60px' },
];

const HMRC_CATEGORIES = [
  'Office costs',
  'Travel costs',
  'Clothing expenses',
  'Staff costs',
  'Things you buy to resell',
  'Financial costs',
  'Business premises costs',
  'Advertising & marketing',
  'Training courses',
  'Legal & professional fees',
  'Phone, internet & software',
  'Insurance',
  'Vehicle expenses',
  'Capital allowances',
  'Other allowable expenses',
];

const DEFAULT_EXPENSE = {
  date: new Date().toISOString().slice(0, 10),
  description: '',
  supplier: '',
  amount: '',
  currency: 'GBP',
  category: '',
  allowable_pct: '100',
  notes: '',
  has_receipt: false,
};

export default function Expenses({ activeModule, onModuleChange }) {
  const [activePanel, setActivePanel] = useState('all');
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [form, setForm] = useState({ ...DEFAULT_EXPENSE });
  const [receiptFile, setReceiptFile] = useState(null);
  const fileRef = useRef(null);

  const handleSidebarChange = useCallback((key) => {
    if (key === 'add') {
      setShowAddModal(true);
      return;
    }
    if (key === 'scan') {
      if (fileRef.current) fileRef.current.click();
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
        const data = await getTransactions({ type: 'expense' });
        if (!cancelled) setExpenses(Array.isArray(data) ? data : []);
      } catch {
        if (!cancelled) setExpenses([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const updateForm = (field) => (val) => setForm((prev) => ({ ...prev, [field]: val }));

  const handleAddExpense = async () => {
    if (!form.description || !form.amount) return;
    try {
      const tx = await createTransaction({
        ...form,
        type: 'expense',
        amount: parseFloat(form.amount),
        allowable_pct: parseFloat(form.allowable_pct),
        has_receipt: !!receiptFile,
      });
      setExpenses((prev) => [tx, ...prev]);
    } catch {
      setExpenses((prev) => [
        {
          ...form,
          id: Date.now(),
          type: 'expense',
          amount: parseFloat(form.amount),
          has_receipt: !!receiptFile,
        },
        ...prev,
      ]);
    }
    setForm({ ...DEFAULT_EXPENSE });
    setReceiptFile(null);
    setShowAddModal(false);
  };

  const handleReceiptScan = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      await scanReceipt(file);
    } catch {
      // API unavailable
    }
  };

  const totalExpenses = expenses.reduce((s, t) => s + (parseFloat(t.amount) || 0), 0);

  const byCategory = expenses.reduce((acc, t) => {
    const cat = t.category || 'Uncategorised';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(t);
    return acc;
  }, {});

  const withReceipts = expenses.filter((t) => t.has_receipt);

  const fmt = (n) => `\u00a3${n.toLocaleString('en-GB', { minimumFractionDigits: 2 })}`;

  const renderAll = () => (
    <>
      <div className="section-title">All expenses</div>
      <div className="summary-cards">
        <SummaryCard label="Total Expenses YTD" value={fmt(totalExpenses)} variant="warn" />
        <SummaryCard label="Transactions" value={String(expenses.length)} variant="neutral" />
        <SummaryCard label="With receipts" value={String(withReceipts.length)} variant="neutral" />
      </div>
      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <DataTable
          columns={EXPENSE_COLUMNS}
          data={expenses}
          emptyMessage="No expenses recorded yet. Press N to add."
        />
      )}
    </>
  );

  const renderByCategory = () => (
    <>
      <div className="section-title">Expenses by HMRC category</div>
      {Object.keys(byCategory).length === 0 ? (
        <div className="empty-state">No expense data to group</div>
      ) : (
        Object.entries(byCategory).map(([cat, items]) => {
          const total = items.reduce((s, t) => s + (parseFloat(t.amount) || 0), 0);
          return (
            <div key={cat}>
              <div className="group-header">{cat}</div>
              <DataTable columns={EXPENSE_COLUMNS} data={items} />
              <div className="group-total">Subtotal: {fmt(total)}</div>
            </div>
          );
        })
      )}
    </>
  );

  const renderReceipts = () => (
    <>
      <div className="section-title">Expenses with receipts</div>
      <DataTable
        columns={EXPENSE_COLUMNS}
        data={withReceipts}
        emptyMessage="No receipts attached to any expenses"
      />
    </>
  );

  const panels = { all: renderAll, 'by-category': renderByCategory, receipts: renderReceipts };

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

      <input type="file" ref={fileRef} style={{ display: 'none' }} accept="image/*,.pdf" onChange={handleReceiptScan} />

      <Modal isOpen={showAddModal} onClose={() => setShowAddModal(false)} title="Add Expense">
        <div className="form-row">
          <FormInput label="Date" type="date" value={form.date} onChange={updateForm('date')} size="small" />
          <FormInput label="Supplier" type="text" value={form.supplier} onChange={updateForm('supplier')} placeholder="Company name" size="medium" />
        </div>
        <div style={{ marginTop: 12 }}>
          <FormInput label="Description" type="text" value={form.description} onChange={updateForm('description')} placeholder="What was purchased?" />
        </div>
        <div className="form-row" style={{ marginTop: 12 }}>
          <FormInput label="Amount" type="number" value={form.amount} onChange={updateForm('amount')} placeholder="0.00" step="0.01" size="small" />
          <FormInput label="Currency" type="select" value={form.currency} onChange={updateForm('currency')} options={['GBP', 'USD', 'EUR']} size="small" />
          <FormInput label="Category" type="select" value={form.category} onChange={updateForm('category')} options={HMRC_CATEGORIES} placeholder="HMRC category" size="medium" />
        </div>
        <div className="form-row" style={{ marginTop: 12 }}>
          <FormInput label="Allowable %" type="number" value={form.allowable_pct} onChange={updateForm('allowable_pct')} min="0" max="100" step="1" size="small" />
        </div>
        <div style={{ marginTop: 12 }}>
          <div className="form-label" style={{ marginBottom: 4 }}>RECEIPT</div>
          <div
            className={`file-upload-area${receiptFile ? ' dragover' : ''}`}
            onClick={() => {
              const input = document.createElement('input');
              input.type = 'file';
              input.accept = 'image/*,.pdf';
              input.onchange = (e) => setReceiptFile(e.target.files?.[0] || null);
              input.click();
            }}
          >
            {receiptFile ? receiptFile.name : 'Click to attach receipt or drag & drop'}
          </div>
        </div>
        <div style={{ marginTop: 12 }}>
          <FormInput label="Notes" type="textarea" value={form.notes} onChange={updateForm('notes')} placeholder="Optional notes..." />
        </div>
        <div className="modal-footer" style={{ padding: '12px 0 0', borderTop: 'none' }}>
          <button className="btn btn-ghost" onClick={() => setShowAddModal(false)}>Cancel</button>
          <button className="btn btn-primary" onClick={handleAddExpense}>Save expense</button>
        </div>
      </Modal>
    </Layout>
  );
}
