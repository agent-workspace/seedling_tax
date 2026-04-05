import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import FormInput from '../components/FormInput';
import DataTable from '../components/DataTable';
import Modal from '../components/Modal';
import useKeyboard from '../hooks/useKeyboard';
import { getSettings, updateSettings, getCategories, createCategory, getImportProfiles } from '../api/client';

const SIDEBAR_ITEMS = [
  { key: 'general', label: 'General', shortcut: '1' },
  { key: 'ai-config', label: 'AI config', shortcut: '2' },
  { key: 'categories', label: 'Categories', shortcut: '3' },
  { key: 'invoice-settings', label: 'Invoice settings', shortcut: '4' },
  { key: 'import-profiles', label: 'Import profiles', shortcut: '5' },
  { key: 'hmrc-knowledge', label: 'HMRC knowledge', shortcut: '6' },
];

const STATUS_HINTS = [
  { key: 'Alt+S', label: 'Settings' },
  { key: '1-6', label: 'Navigate' },
  { key: '?', label: 'Shortcuts' },
];

const DEFAULT_GENERAL = {
  business_name: '',
  address: '',
  entity_type: 'sole_trader',
  utr_number: '',
  company_number: '',
  vat_number: '',
};

const DEFAULT_AI = {
  fast_model: 'gpt-4o-mini',
  smart_model: 'gpt-4o',
  api_key: '',
};

const DEFAULT_INVOICE = {
  prefix: 'INV',
  payment_terms: '30',
  bank_details: '',
};

export default function Settings({ activeModule, onModuleChange }) {
  const [activePanel, setActivePanel] = useState('general');
  const [general, setGeneral] = useState({ ...DEFAULT_GENERAL });
  const [aiConfig, setAiConfig] = useState({ ...DEFAULT_AI });
  const [invoiceSettings, setInvoiceSettings] = useState({ ...DEFAULT_INVOICE });
  const [categories, setCategories] = useState([]);
  const [importProfiles, setImportProfiles] = useState([]);
  const [hmrcKnowledge, setHmrcKnowledge] = useState('');
  const [newCategory, setNewCategory] = useState('');
  const [showCatModal, setShowCatModal] = useState(false);
  const [editingCatIdx, setEditingCatIdx] = useState(null);
  const [editCatName, setEditCatName] = useState('');
  const [saved, setSaved] = useState(false);

  const handleSidebarChange = useCallback((key) => {
    setActivePanel(key);
  }, []);

  useKeyboard({
    onNumberKey: (num) => {
      const item = SIDEBAR_ITEMS[num - 1];
      if (item) handleSidebarChange(item.key);
    },
    onEscape: () => setShowCatModal(false),
  });

  useEffect(() => {
    async function load() {
      try {
        const [gen, ai, inv, cats, profiles, hmrc] = await Promise.all([
          getSettings('general').catch(() => null),
          getSettings('ai').catch(() => null),
          getSettings('invoice').catch(() => null),
          getCategories().catch(() => []),
          getImportProfiles().catch(() => []),
          getSettings('hmrc_knowledge').catch(() => null),
        ]);
        if (gen) setGeneral((prev) => ({ ...prev, ...gen }));
        if (ai) setAiConfig((prev) => ({ ...prev, ...ai }));
        if (inv) setInvoiceSettings((prev) => ({ ...prev, ...inv }));
        if (Array.isArray(cats)) setCategories(cats.map((c) => (typeof c === 'string' ? c : c.name || c.label || '')));
        if (Array.isArray(profiles)) setImportProfiles(profiles);
        if (hmrc && hmrc.value) setHmrcKnowledge(hmrc.value);
      } catch {
        // API unavailable, use defaults
      }
    }
    load();
  }, []);

  const updateGeneral = (field) => (val) => setGeneral((prev) => ({ ...prev, [field]: val }));
  const updateAi = (field) => (val) => setAiConfig((prev) => ({ ...prev, [field]: val }));
  const updateInv = (field) => (val) => setInvoiceSettings((prev) => ({ ...prev, [field]: val }));

  const showSavedFeedback = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const saveGeneral = async () => {
    try { await updateSettings('general', general); } catch { /* offline */ }
    showSavedFeedback();
  };

  const saveAi = async () => {
    try { await updateSettings('ai', aiConfig); } catch { /* offline */ }
    showSavedFeedback();
  };

  const saveInvoice = async () => {
    try { await updateSettings('invoice', invoiceSettings); } catch { /* offline */ }
    showSavedFeedback();
  };

  const saveHmrc = async () => {
    try { await updateSettings('hmrc_knowledge', { value: hmrcKnowledge }); } catch { /* offline */ }
    showSavedFeedback();
  };

  const addCategory = async () => {
    if (!newCategory.trim()) return;
    try { await createCategory({ name: newCategory.trim() }); } catch { /* offline */ }
    setCategories((prev) => [...prev, newCategory.trim()]);
    setNewCategory('');
    setShowCatModal(false);
  };

  const deleteCategory = (idx) => {
    setCategories((prev) => prev.filter((_, i) => i !== idx));
  };

  const startEditCategory = (idx) => {
    setEditingCatIdx(idx);
    setEditCatName(categories[idx]);
  };

  const saveEditCategory = () => {
    if (editingCatIdx === null) return;
    setCategories((prev) => prev.map((c, i) => (i === editingCatIdx ? editCatName : c)));
    setEditingCatIdx(null);
    setEditCatName('');
  };

  const renderGeneral = () => (
    <>
      <div className="section-title">General settings</div>
      <div className="settings-section">
        <h3>Business details</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <FormInput label="Business name" value={general.business_name} onChange={updateGeneral('business_name')} placeholder="Your business name" />
          <FormInput label="Address" type="textarea" value={general.address} onChange={updateGeneral('address')} placeholder="Business address" rows={3} />
          <FormInput
            label="Entity type"
            type="select"
            value={general.entity_type}
            onChange={updateGeneral('entity_type')}
            options={[
              { value: 'sole_trader', label: 'Sole Trader' },
              { value: 'ltd', label: 'LTD Company' },
            ]}
            size="medium"
          />
          <FormInput label="UTR number" value={general.utr_number} onChange={updateGeneral('utr_number')} placeholder="Unique Taxpayer Reference" size="medium" />
          {general.entity_type === 'ltd' && (
            <FormInput label="Company number" value={general.company_number} onChange={updateGeneral('company_number')} placeholder="Companies House number" size="medium" />
          )}
          <FormInput label="VAT number" value={general.vat_number} onChange={updateGeneral('vat_number')} placeholder="VAT registration number (if registered)" size="medium" />
        </div>
        <div className="form-actions" style={{ marginTop: 16 }}>
          <button className="btn btn-primary" onClick={saveGeneral}>Save</button>
          {saved && <span style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>Saved</span>}
        </div>
      </div>
    </>
  );

  const renderAiConfig = () => (
    <>
      <div className="section-title">AI configuration</div>
      <div className="settings-section">
        <h3>Model settings</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <FormInput label="Fast model" value={aiConfig.fast_model} onChange={updateAi('fast_model')} placeholder="e.g. gpt-4o-mini" size="medium" />
          <FormInput label="Smart model" value={aiConfig.smart_model} onChange={updateAi('smart_model')} placeholder="e.g. gpt-4o" size="medium" />
          <FormInput label="API key" type="password" value={aiConfig.api_key} onChange={updateAi('api_key')} placeholder="sk-..." size="medium" />
        </div>
        <div className="form-actions" style={{ marginTop: 16 }}>
          <button className="btn btn-primary" onClick={saveAi}>Save</button>
          {saved && <span style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>Saved</span>}
        </div>
      </div>
    </>
  );

  const renderCategories = () => (
    <>
      <div className="section-title">Categories</div>
      <div className="settings-section">
        <div className="category-list">
          {categories.length === 0 && (
            <div className="empty-state">No categories configured. Add one below.</div>
          )}
          {categories.map((cat, idx) => (
            <div key={idx} className="category-item">
              {editingCatIdx === idx ? (
                <div style={{ display: 'flex', gap: 8, flex: 1 }}>
                  <input
                    className="form-input"
                    value={editCatName}
                    onChange={(e) => setEditCatName(e.target.value)}
                    style={{ flex: 1 }}
                    autoFocus
                    onKeyDown={(e) => e.key === 'Enter' && saveEditCategory()}
                  />
                  <button className="btn btn-primary btn-sm" onClick={saveEditCategory}>Save</button>
                  <button className="btn btn-ghost btn-sm" onClick={() => setEditingCatIdx(null)}>Cancel</button>
                </div>
              ) : (
                <>
                  <span className="category-item-name">{cat}</span>
                  <div className="category-item-actions">
                    <button className="btn btn-ghost btn-sm" onClick={() => startEditCategory(idx)}>Edit</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => deleteCategory(idx)}>Delete</button>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
        <div className="form-actions" style={{ marginTop: 16 }}>
          <button className="btn btn-primary" onClick={() => setShowCatModal(true)}>Add category</button>
        </div>
      </div>

      <Modal isOpen={showCatModal} onClose={() => setShowCatModal(false)} title="Add Category">
        <FormInput label="Category name" value={newCategory} onChange={setNewCategory} placeholder="e.g. Office supplies" />
        <div className="modal-footer" style={{ padding: '12px 0 0', borderTop: 'none' }}>
          <button className="btn btn-ghost" onClick={() => setShowCatModal(false)}>Cancel</button>
          <button className="btn btn-primary" onClick={addCategory}>Add</button>
        </div>
      </Modal>
    </>
  );

  const renderInvoiceSettings = () => (
    <>
      <div className="section-title">Invoice settings</div>
      <div className="settings-section">
        <h3>Defaults</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <FormInput label="Invoice prefix" value={invoiceSettings.prefix} onChange={updateInv('prefix')} placeholder="INV" size="small" />
          <FormInput label="Default payment terms (days)" type="number" value={invoiceSettings.payment_terms} onChange={updateInv('payment_terms')} size="small" />
          <FormInput label="Bank details" type="textarea" value={invoiceSettings.bank_details} onChange={updateInv('bank_details')} placeholder="Sort code: XX-XX-XX&#10;Account: XXXXXXXX&#10;IBAN: ..." rows={5} />
        </div>
        <div className="form-actions" style={{ marginTop: 16 }}>
          <button className="btn btn-primary" onClick={saveInvoice}>Save</button>
          {saved && <span style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>Saved</span>}
        </div>
      </div>
    </>
  );

  const renderImportProfiles = () => (
    <>
      <div className="section-title">Import profiles</div>
      <div className="settings-section">
        {importProfiles.length === 0 ? (
          <div className="empty-state">No import profiles configured. Import a bank statement to create one.</div>
        ) : (
          <DataTable
            columns={[
              { key: 'name', label: 'Profile name' },
              { key: 'bank', label: 'Bank', width: '140px' },
              { key: 'format', label: 'Format', width: '80px' },
              { key: 'last_used', label: 'Last used', type: 'date', width: '110px' },
            ]}
            data={importProfiles}
            emptyMessage="No profiles"
          />
        )}
      </div>
    </>
  );

  const renderHmrcKnowledge = () => (
    <>
      <div className="section-title">HMRC knowledge base</div>
      <div className="settings-section">
        <p style={{ color: 'var(--text-dimmed)', fontSize: 13, marginBottom: 12 }}>
          Editable knowledge base of HMRC tax rules used by the AI for categorisation and tax calculations. Updates here will influence AI suggestions.
        </p>
        <FormInput
          label="Tax rules knowledge"
          type="textarea"
          value={hmrcKnowledge || `# HMRC Tax Rules - 2025/26

## Income Tax Bands
- Personal Allowance: \u00a30 - \u00a312,570 (0%)
- Basic Rate: \u00a312,571 - \u00a350,270 (20%)
- Higher Rate: \u00a350,271 - \u00a3125,140 (40%)
- Additional Rate: Over \u00a3125,140 (45%)

## National Insurance (Class 4)
- Below \u00a312,570: 0%
- \u00a312,571 - \u00a350,270: 6%
- Over \u00a350,270: 2%
- Class 2: \u00a33.45/week (if profits > \u00a312,570)

## Allowable Expenses
- Office costs (stationery, phone bills)
- Travel costs (fuel, parking, bus/train fares)
- Clothing expenses (uniforms, protective clothing)
- Staff costs (salaries, subcontractor costs)
- Financial costs (insurance, bank charges)
- Business premises costs (rent, utilities)
- Advertising and marketing
- Professional fees (accountant, solicitor)

## Simplified Expenses
- Working from home: \u00a326/month (25-50 hrs), \u00a318/month (51-100 hrs), \u00a310/month (101+ hrs)
- Business mileage: 45p/mile first 10,000; 25p/mile after

## VAT Threshold
- Registration threshold: \u00a385,000
- Deregistration threshold: \u00a383,000`}
          onChange={setHmrcKnowledge}
          rows={20}
        />
        <div className="form-actions" style={{ marginTop: 16 }}>
          <button className="btn btn-primary" onClick={saveHmrc}>Save</button>
          {saved && <span style={{ color: 'var(--accent)', fontFamily: 'var(--font-mono)', fontSize: 13 }}>Saved</span>}
        </div>
      </div>
    </>
  );

  const panels = {
    general: renderGeneral,
    'ai-config': renderAiConfig,
    categories: renderCategories,
    'invoice-settings': renderInvoiceSettings,
    'import-profiles': renderImportProfiles,
    'hmrc-knowledge': renderHmrcKnowledge,
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
      {(panels[activePanel] || renderGeneral)()}
    </Layout>
  );
}
