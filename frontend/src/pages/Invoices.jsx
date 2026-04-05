import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import DataTable from '../components/DataTable';
import FormInput from '../components/FormInput';
import Modal from '../components/Modal';
import useKeyboard from '../hooks/useKeyboard';
import { getInvoices, createInvoice } from '../api/client';

const SIDEBAR_ITEMS = [
  { key: 'outgoing', label: 'Outgoing', shortcut: '1' },
  { key: 'incoming', label: 'Incoming', shortcut: '2' },
  { key: 'drafts', label: 'Drafts', shortcut: '3' },
  { key: 'overdue', label: 'Overdue', shortcut: '4' },
  { divider: true },
  { key: 'new', label: 'New invoice...', shortcut: 'N' },
];

const STATUS_HINTS = [
  { key: 'Alt+V', label: 'Invoices' },
  { key: '1-4', label: 'Navigate' },
  { key: 'N', label: 'New invoice' },
  { key: '?', label: 'Shortcuts' },
];

const INVOICE_COLUMNS = [
  { key: 'number', label: 'Invoice #', width: '110px' },
  { key: 'client', label: 'Client' },
  { key: 'date', label: 'Date', type: 'date', width: '100px' },
  { key: 'due_date', label: 'Due', type: 'date', width: '100px' },
  { key: 'total', label: 'Total', type: 'currency', width: '110px' },
  { key: 'status', label: 'Status', type: 'status', width: '90px' },
];

const EMPTY_LINE = { description: '', qty: '1', unit_price: '', tax: '0' };

const DEFAULT_INVOICE = {
  client_name: '',
  client_address: '',
  client_email: '',
  lines: [{ ...EMPTY_LINE }],
  payment_terms: '30',
  due_date: '',
  notes: '',
};

export default function Invoices({ activeModule, onModuleChange }) {
  const [activePanel, setActivePanel] = useState('outgoing');
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewModal, setShowNewModal] = useState(false);
  const [form, setForm] = useState({ ...DEFAULT_INVOICE });

  const handleSidebarChange = useCallback((key) => {
    if (key === 'new') {
      setShowNewModal(true);
      return;
    }
    setActivePanel(key);
  }, []);

  useKeyboard({
    onNumberKey: (num) => {
      const item = SIDEBAR_ITEMS.filter((i) => !i.divider)[num - 1];
      if (item) handleSidebarChange(item.key);
    },
    onEscape: () => setShowNewModal(false),
  });

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await getInvoices();
        if (!cancelled) setInvoices(Array.isArray(data) ? data : []);
      } catch {
        if (!cancelled) setInvoices([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const updateForm = (field) => (val) => setForm((prev) => ({ ...prev, [field]: val }));

  const updateLine = (idx, field, val) => {
    setForm((prev) => {
      const lines = [...prev.lines];
      lines[idx] = { ...lines[idx], [field]: val };
      return { ...prev, lines };
    });
  };

  const addLine = () => {
    setForm((prev) => ({ ...prev, lines: [...prev.lines, { ...EMPTY_LINE }] }));
  };

  const removeLine = (idx) => {
    setForm((prev) => ({
      ...prev,
      lines: prev.lines.length > 1 ? prev.lines.filter((_, i) => i !== idx) : prev.lines,
    }));
  };

  const lineTotal = (line) => {
    const sub = (parseFloat(line.qty) || 0) * (parseFloat(line.unit_price) || 0);
    const tax = sub * ((parseFloat(line.tax) || 0) / 100);
    return sub + tax;
  };

  const invoiceTotal = form.lines.reduce((s, l) => s + lineTotal(l), 0);

  const handleCreateInvoice = async () => {
    if (!form.client_name) return;
    const invoiceData = {
      ...form,
      total: invoiceTotal,
      status: 'Draft',
      date: new Date().toISOString().slice(0, 10),
      number: `INV-${String(invoices.length + 1).padStart(4, '0')}`,
      client: form.client_name,
    };
    try {
      const saved = await createInvoice(invoiceData);
      setInvoices((prev) => [saved, ...prev]);
    } catch {
      setInvoices((prev) => [{ ...invoiceData, id: Date.now() }, ...prev]);
    }
    setForm({ ...DEFAULT_INVOICE, lines: [{ ...EMPTY_LINE }] });
    setShowNewModal(false);
  };

  const outgoing = invoices.filter((inv) => inv.direction !== 'incoming');
  const incoming = invoices.filter((inv) => inv.direction === 'incoming');
  const drafts = invoices.filter((inv) => (inv.status || '').toLowerCase() === 'draft');
  const overdue = invoices.filter((inv) => (inv.status || '').toLowerCase() === 'overdue');

  const fmt = (n) => `\u00a3${(parseFloat(n) || 0).toLocaleString('en-GB', { minimumFractionDigits: 2 })}`;

  const renderPanel = (title, data, empty) => (
    <>
      <div className="section-title">{title}</div>
      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <DataTable columns={INVOICE_COLUMNS} data={data} emptyMessage={empty} />
      )}
    </>
  );

  const panels = {
    outgoing: () => renderPanel('Outgoing invoices', outgoing, 'No outgoing invoices yet'),
    incoming: () => renderPanel('Incoming invoices', incoming, 'No incoming invoices yet'),
    drafts: () => renderPanel('Draft invoices', drafts, 'No drafts'),
    overdue: () => renderPanel('Overdue invoices', overdue, 'No overdue invoices'),
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
      {(panels[activePanel] || panels.outgoing)()}

      <Modal isOpen={showNewModal} onClose={() => setShowNewModal(false)} title="New Invoice">
        <div className="form-row">
          <FormInput label="Client name" type="text" value={form.client_name} onChange={updateForm('client_name')} placeholder="Client / Company name" />
        </div>
        <div style={{ marginTop: 12 }}>
          <FormInput label="Client address" type="textarea" value={form.client_address} onChange={updateForm('client_address')} placeholder="Full address" rows={2} />
        </div>
        <div className="form-row" style={{ marginTop: 12 }}>
          <FormInput label="Client email" type="email" value={form.client_email} onChange={updateForm('client_email')} placeholder="email@example.com" size="medium" />
          <FormInput label="Payment terms (days)" type="number" value={form.payment_terms} onChange={updateForm('payment_terms')} size="small" />
          <FormInput label="Due date" type="date" value={form.due_date} onChange={updateForm('due_date')} size="small" />
        </div>

        <div className="section-subtitle" style={{ marginTop: 16, marginBottom: 8 }}>Line items</div>
        <table className="line-items-table">
          <thead>
            <tr>
              <th>Description</th>
              <th style={{ width: 60 }}>Qty</th>
              <th style={{ width: 100 }}>Unit price</th>
              <th style={{ width: 70 }}>Tax %</th>
              <th style={{ width: 90 }}>Total</th>
              <th style={{ width: 30 }}></th>
            </tr>
          </thead>
          <tbody>
            {form.lines.map((line, idx) => (
              <tr key={idx}>
                <td>
                  <input value={line.description} onChange={(e) => updateLine(idx, 'description', e.target.value)} placeholder="Service / product" />
                </td>
                <td>
                  <input type="number" value={line.qty} onChange={(e) => updateLine(idx, 'qty', e.target.value)} min="1" step="1" />
                </td>
                <td>
                  <input type="number" value={line.unit_price} onChange={(e) => updateLine(idx, 'unit_price', e.target.value)} placeholder="0.00" step="0.01" />
                </td>
                <td>
                  <input type="number" value={line.tax} onChange={(e) => updateLine(idx, 'tax', e.target.value)} placeholder="0" step="1" />
                </td>
                <td style={{ fontFamily: 'var(--font-mono)', textAlign: 'right', fontSize: 13 }}>
                  {fmt(lineTotal(line))}
                </td>
                <td>
                  <button className="btn btn-ghost btn-sm" onClick={() => removeLine(idx)} title="Remove">&times;</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
          <button className="btn btn-secondary btn-sm" onClick={addLine}>+ Add line</button>
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 500, fontSize: 14 }}>
            Total: {fmt(invoiceTotal)}
          </span>
        </div>

        <div style={{ marginTop: 12 }}>
          <FormInput label="Notes" type="textarea" value={form.notes} onChange={updateForm('notes')} placeholder="Payment details, thank you note..." />
        </div>
        <div className="modal-footer" style={{ padding: '12px 0 0', borderTop: 'none' }}>
          <button className="btn btn-ghost" onClick={() => setShowNewModal(false)}>Cancel</button>
          <button className="btn btn-secondary" onClick={handleCreateInvoice}>Save as draft</button>
          <button className="btn btn-primary" onClick={handleCreateInvoice}>Create & send</button>
        </div>
      </Modal>
    </Layout>
  );
}
