import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import SummaryCard from '../components/SummaryCard';
import FormInput from '../components/FormInput';
import DataTable from '../components/DataTable';
import useKeyboard from '../hooks/useKeyboard';
import { getTransactions, createTransaction, getCategories } from '../api/client';

const SIDEBAR_ITEMS = [
  { key: 'overview', label: 'Overview', shortcut: '1' },
  { key: 'recent', label: 'Recent activity', shortcut: '2' },
  { key: 'monthly', label: 'Monthly summary', shortcut: '3' },
  { key: 'insights', label: 'Agent insights', shortcut: '4' },
  { divider: true },
  { key: 'quick-add', label: 'Quick add...', shortcut: 'N' },
  { key: 'import', label: 'Import data...', shortcut: 'Ctrl+I' },
  { key: 'scan', label: 'Scan receipt...', shortcut: 'Ctrl+R' },
];

const STATUS_HINTS = [
  { key: 'Alt+D', label: 'Dashboard' },
  { key: '1-4', label: 'Navigate' },
  { key: 'N', label: 'Quick add' },
  { key: '?', label: 'Shortcuts' },
];

const TRANSACTION_COLUMNS = [
  { key: 'date', label: 'Date', type: 'date', width: '100px' },
  { key: 'description', label: 'Description' },
  { key: 'category', label: 'Category', width: '140px' },
  { key: 'amount', label: 'Amount', type: 'currency', width: '110px' },
];

const DEFAULT_FORM = {
  type: 'expense',
  date: new Date().toISOString().slice(0, 10),
  description: '',
  category: '',
  amount: '',
  currency: 'GBP',
};

export default function Dashboard({ activeModule, onModuleChange }) {
  const [activePanel, setActivePanel] = useState('overview');
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ ...DEFAULT_FORM });

  const handleSidebarChange = useCallback((key) => {
    if (key === 'quick-add') {
      setActivePanel('overview');
      return;
    }
    setActivePanel(key);
  }, []);

  useKeyboard({
    onNumberKey: (num) => {
      const item = SIDEBAR_ITEMS.filter((i) => !i.divider)[num - 1];
      if (item) handleSidebarChange(item.key);
    },
  });

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [txData, catData] = await Promise.all([getTransactions(), getCategories()]);
        if (!cancelled) {
          setTransactions(Array.isArray(txData) ? txData : []);
          setCategories(Array.isArray(catData) ? catData : []);
        }
      } catch {
        if (!cancelled) {
          setTransactions([]);
          setCategories([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const updateForm = (field) => (val) => setForm((prev) => ({ ...prev, [field]: val }));

  const handleSave = async () => {
    if (!form.description || !form.amount) return;
    try {
      const tx = await createTransaction({
        ...form,
        amount: parseFloat(form.amount),
      });
      setTransactions((prev) => [tx, ...prev]);
      setForm({ ...DEFAULT_FORM });
    } catch {
      // API unavailable
    }
  };

  const handleCancel = () => setForm({ ...DEFAULT_FORM });

  const incomeYTD = transactions
    .filter((t) => t.type === 'income')
    .reduce((sum, t) => sum + (parseFloat(t.amount) || 0), 0);
  const expenseYTD = transactions
    .filter((t) => t.type === 'expense')
    .reduce((sum, t) => sum + (parseFloat(t.amount) || 0), 0);
  const estTax = Math.max(0, (incomeYTD - expenseYTD) * 0.2);

  const recentTx = transactions.slice(0, 10);

  const categoryOptions = categories.map((c) => (typeof c === 'string' ? c : c.name || c.label || ''));

  const renderOverview = () => (
    <>
      <div className="summary-cards">
        <SummaryCard label="Income YTD" value={`\u00a3${incomeYTD.toLocaleString('en-GB', { minimumFractionDigits: 2 })}`} variant="good" />
        <SummaryCard label="Expenses YTD" value={`\u00a3${expenseYTD.toLocaleString('en-GB', { minimumFractionDigits: 2 })}`} variant="warn" />
        <SummaryCard label="Est. Tax Owed" value={`\u00a3${estTax.toLocaleString('en-GB', { minimumFractionDigits: 2 })}`} variant="neutral" />
      </div>

      <div className="quick-add-form">
        <div className="section-title">Quick add transaction</div>
        <div className="form-row">
          <FormInput
            label="Type"
            type="select"
            value={form.type}
            onChange={updateForm('type')}
            options={[
              { value: 'income', label: 'Income' },
              { value: 'expense', label: 'Expense' },
            ]}
            size="small"
          />
          <FormInput
            label="Date"
            type="date"
            value={form.date}
            onChange={updateForm('date')}
            size="small"
          />
          <FormInput
            label="Description"
            type="text"
            value={form.description}
            onChange={updateForm('description')}
            placeholder="What was it for?"
            size="full"
          />
        </div>
        <div className="form-row" style={{ marginTop: 12 }}>
          <FormInput
            label="Category"
            type="select"
            value={form.category}
            onChange={updateForm('category')}
            options={categoryOptions.length ? categoryOptions : ['Office costs', 'Travel', 'Phone & internet', 'Professional fees', 'Other']}
            placeholder="Select category"
            size="medium"
          />
          <FormInput
            label="Amount"
            type="number"
            value={form.amount}
            onChange={updateForm('amount')}
            placeholder="0.00"
            step="0.01"
            min="0"
            size="small"
          />
          <FormInput
            label="Currency"
            type="select"
            value={form.currency}
            onChange={updateForm('currency')}
            options={['GBP', 'USD', 'EUR']}
            size="small"
          />
        </div>
        <div className="form-actions">
          <button className="btn btn-primary" onClick={handleSave}>Save</button>
          <button className="btn btn-secondary">Attach receipt</button>
          <button className="btn btn-ghost" onClick={handleCancel}>Cancel</button>
        </div>
      </div>

      <div className="section-title">Recent transactions</div>
      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <DataTable
          columns={TRANSACTION_COLUMNS}
          data={recentTx}
          emptyMessage="No transactions yet. Use the form above to add one."
        />
      )}
    </>
  );

  const renderRecent = () => (
    <>
      <div className="section-title">Recent activity</div>
      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <DataTable
          columns={TRANSACTION_COLUMNS}
          data={transactions.slice(0, 20)}
          emptyMessage="No recent activity"
        />
      )}
    </>
  );

  const renderMonthly = () => {
    const now = new Date();
    const monthStr = now.toLocaleString('en-GB', { month: 'long', year: 'numeric' });
    const monthTx = transactions.filter((t) => {
      const d = new Date(t.date);
      return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
    });
    const mIncome = monthTx.filter((t) => t.type === 'income').reduce((s, t) => s + (parseFloat(t.amount) || 0), 0);
    const mExpense = monthTx.filter((t) => t.type === 'expense').reduce((s, t) => s + (parseFloat(t.amount) || 0), 0);
    const mProfit = mIncome - mExpense;

    return (
      <>
        <div className="section-title">Monthly summary - {monthStr}</div>
        <div className="summary-cards">
          <SummaryCard label="Income" value={`\u00a3${mIncome.toLocaleString('en-GB', { minimumFractionDigits: 2 })}`} variant="good" />
          <SummaryCard label="Expenses" value={`\u00a3${mExpense.toLocaleString('en-GB', { minimumFractionDigits: 2 })}`} variant="warn" />
          <SummaryCard label="Profit" value={`\u00a3${mProfit.toLocaleString('en-GB', { minimumFractionDigits: 2 })}`} variant={mProfit >= 0 ? 'good' : 'warn'} />
        </div>
        <DataTable
          columns={TRANSACTION_COLUMNS}
          data={monthTx}
          emptyMessage="No transactions this month"
        />
      </>
    );
  };

  const renderInsights = () => (
    <>
      <div className="section-title">Agent insights</div>
      <div className="panel-box">
        <div className="insight-item">
          <span className="insight-icon">!</span>
          <span className="insight-text">
            <span className="highlight">3 uncategorised transactions</span> need attention. Review them in Expenses.
          </span>
        </div>
        <div className="insight-item">
          <span className="insight-icon">%</span>
          <span className="insight-text">
            VAT threshold: <span className="highlight">42% of limit reached</span> (\u00a336,120 of \u00a385,000). Consider voluntary registration.
          </span>
        </div>
        <div className="insight-item">
          <span className="insight-icon">$</span>
          <span className="insight-text">
            Payment on account due <span className="highlight">31 January 2026</span>. Estimated: \u00a32,450.
          </span>
        </div>
        <div className="insight-item">
          <span className="insight-icon">R</span>
          <span className="insight-text">
            <span className="highlight">5 expenses</span> are missing receipts. Attach them for compliance.
          </span>
        </div>
      </div>
    </>
  );

  const panels = {
    overview: renderOverview,
    recent: renderRecent,
    monthly: renderMonthly,
    insights: renderInsights,
  };

  return (
    <Layout
      activeModule={activeModule}
      onModuleChange={onModuleChange}
      sidebarItems={SIDEBAR_ITEMS}
      activeSidebarItem={activePanel}
      onSidebarChange={handleSidebarChange}
      statusHints={STATUS_HINTS}
    >
      {(panels[activePanel] || renderOverview)()}
    </Layout>
  );
}
