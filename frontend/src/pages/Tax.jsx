import React, { useState, useEffect, useCallback } from 'react';
import Layout from '../components/Layout';
import SummaryCard from '../components/SummaryCard';
import DataTable from '../components/DataTable';
import useKeyboard from '../hooks/useKeyboard';
import { getTaxSummary, getSelfAssessment, getPAYESummary } from '../api/client';

const SIDEBAR_ITEMS = [
  { key: 'overview', label: 'Overview', shortcut: '1' },
  { key: 'self-employment', label: 'Self-employment', shortcut: '2' },
  { key: 'paye-summary', label: 'PAYE summary', shortcut: '3' },
  { key: 'self-assessment', label: 'Self Assessment', shortcut: '4' },
  { key: 'hmrc-rates', label: 'HMRC rates', shortcut: '5' },
];

const STATUS_HINTS = [
  { key: 'Alt+T', label: 'Tax' },
  { key: '1-5', label: 'Navigate' },
  { key: '?', label: 'Shortcuts' },
];

const TAX_BANDS_25_26 = [
  { band: 'Personal Allowance', from: 0, to: 12570, rate: '0%' },
  { band: 'Basic rate', from: 12571, to: 50270, rate: '20%' },
  { band: 'Higher rate', from: 50271, to: 125140, rate: '40%' },
  { band: 'Additional rate', from: 125141, to: null, rate: '45%' },
];

const NI_RATES = [
  { band: 'Below threshold', from: 0, to: 12570, rate: '0%' },
  { band: 'Class 4 main', from: 12571, to: 50270, rate: '6%' },
  { band: 'Class 4 upper', from: 50271, to: null, rate: '2%' },
];

export default function Tax({ activeModule, onModuleChange }) {
  const [activePanel, setActivePanel] = useState('overview');
  const [taxData, setTaxData] = useState(null);
  const [payeSummary, setPayeSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  const handleSidebarChange = useCallback((key) => {
    setActivePanel(key);
  }, []);

  useKeyboard({
    onNumberKey: (num) => {
      const item = SIDEBAR_ITEMS[num - 1];
      if (item) handleSidebarChange(item.key);
    },
  });

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [tax, paye] = await Promise.all([getTaxSummary(), getPAYESummary()]);
        if (!cancelled) {
          setTaxData(tax);
          setPayeSummary(paye);
        }
      } catch {
        if (!cancelled) {
          setTaxData(null);
          setPayeSummary(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, []);

  const fmt = (n) => `\u00a3${(n || 0).toLocaleString('en-GB', { minimumFractionDigits: 2 })}`;

  const gross = taxData?.gross_income || 0;
  const allowable = taxData?.allowable_expenses || 0;
  const taxableProfit = taxData?.taxable_profit || Math.max(0, gross - allowable);
  const incomeTax = taxData?.income_tax || 0;
  const niContributions = taxData?.ni_contributions || 0;
  const totalTax = taxData?.total_tax || incomeTax + niContributions;
  const effectiveRate = gross > 0 ? ((totalTax / gross) * 100).toFixed(1) : '0.0';

  const renderOverview = () => (
    <>
      <div className="section-title">Tax overview - 2025/26</div>
      <div className="summary-cards">
        <SummaryCard label="Gross Income" value={fmt(gross)} variant="good" />
        <SummaryCard label="Allowable Expenses" value={fmt(allowable)} variant="warn" />
        <SummaryCard label="Taxable Profit" value={fmt(taxableProfit)} variant="neutral" />
      </div>
      <div className="summary-cards">
        <SummaryCard label="Income Tax" value={fmt(incomeTax)} variant="warn" />
        <SummaryCard label="NI Contributions" value={fmt(niContributions)} variant="warn" />
        <SummaryCard label="Total Tax" value={fmt(totalTax)} variant="warn" />
        <SummaryCard label="Effective Rate" value={`${effectiveRate}%`} variant="neutral" />
      </div>

      <div className="section-subtitle" style={{ marginTop: 16 }}>Calculation breakdown</div>
      <table className="tax-calc-table">
        <tbody>
          <tr><td>Gross income</td><td>{fmt(gross)}</td></tr>
          <tr><td>Less: Allowable expenses</td><td>({fmt(allowable)})</td></tr>
          <tr className="subtotal"><td>Taxable profit</td><td>{fmt(taxableProfit)}</td></tr>
          <tr><td>&nbsp;</td><td></td></tr>
          <tr><td>Personal Allowance (up to \u00a312,570)</td><td>0% = {fmt(0)}</td></tr>
          <tr><td>Basic rate (\u00a312,571 - \u00a350,270)</td><td>20%</td></tr>
          <tr><td>Higher rate (\u00a350,271 - \u00a3125,140)</td><td>40%</td></tr>
          <tr className="subtotal"><td>Income tax</td><td>{fmt(incomeTax)}</td></tr>
          <tr><td>&nbsp;</td><td></td></tr>
          <tr><td>Class 2 NI</td><td>{fmt(taxData?.class2_ni || 0)}</td></tr>
          <tr><td>Class 4 NI</td><td>{fmt(taxData?.class4_ni || 0)}</td></tr>
          <tr className="subtotal"><td>National Insurance</td><td>{fmt(niContributions)}</td></tr>
          <tr><td>&nbsp;</td><td></td></tr>
          <tr className="total"><td>Total tax liability</td><td>{fmt(totalTax)}</td></tr>
        </tbody>
      </table>
    </>
  );

  const renderSelfEmployment = () => (
    <>
      <div className="section-title">Self-employment tax calculation</div>
      <div className="section-subtitle">Income tax bands 2025/26</div>
      <DataTable
        columns={[
          { key: 'band', label: 'Band' },
          { key: 'from', label: 'From', type: 'currency', width: '110px' },
          { key: 'to', label: 'To', type: 'currency', width: '110px', render: (r) => r.to ? fmt(r.to) : 'Unlimited' },
          { key: 'rate', label: 'Rate', width: '80px' },
        ]}
        data={TAX_BANDS_25_26}
      />

      <div className="section-subtitle" style={{ marginTop: 16 }}>National Insurance</div>
      <DataTable
        columns={[
          { key: 'band', label: 'Band' },
          { key: 'from', label: 'From', type: 'currency', width: '110px' },
          { key: 'to', label: 'To', type: 'currency', width: '110px', render: (r) => r.to ? fmt(r.to) : 'Unlimited' },
          { key: 'rate', label: 'Rate', width: '80px' },
        ]}
        data={NI_RATES}
      />
    </>
  );

  const renderPayeSummary = () => {
    const entries = payeSummary?.entries || [];
    const totals = payeSummary?.totals || {};

    return (
      <>
        <div className="section-title">PAYE year-to-date</div>
        {entries.length > 0 ? (
          <>
            <DataTable
              columns={[
                { key: 'month', label: 'Month', width: '120px' },
                { key: 'gross_pay', label: 'Gross', type: 'currency', width: '110px' },
                { key: 'tax_deducted', label: 'Tax', type: 'currency', width: '100px' },
                { key: 'ni_deducted', label: 'NI', type: 'currency', width: '100px' },
                { key: 'net_pay', label: 'Net', type: 'currency', width: '110px' },
              ]}
              data={entries}
            />
            <div className="summary-cards" style={{ marginTop: 16 }}>
              <SummaryCard label="Gross YTD" value={fmt(totals.gross_pay || 0)} variant="neutral" />
              <SummaryCard label="Tax YTD" value={fmt(totals.tax_deducted || 0)} variant="warn" />
              <SummaryCard label="Net YTD" value={fmt(totals.net_pay || 0)} variant="good" />
            </div>
          </>
        ) : (
          <div className="empty-state">No PAYE data. Enter payslips in Income &gt; PAYE.</div>
        )}
      </>
    );
  };

  const renderSelfAssessment = () => (
    <>
      <div className="section-title">Self Assessment preparation</div>
      <div className="panel-box">
        <p style={{ marginBottom: 12, color: 'var(--text-dimmed)', fontSize: 13 }}>
          Generate your Self Assessment data for submission to HMRC. Ensure all income and expenses are recorded before exporting.
        </p>
        <div className="summary-cards">
          <SummaryCard label="Status" value="In progress" variant="warn" />
          <SummaryCard label="Tax year" value="2025/26" variant="neutral" />
          <SummaryCard label="Deadline" value="31 Jan 2027" variant="neutral" />
        </div>
        <div className="form-actions" style={{ marginTop: 16 }}>
          <button className="btn btn-primary">Export SA data</button>
          <button className="btn btn-secondary">Review checklist</button>
        </div>
      </div>
    </>
  );

  const renderHmrcRates = () => (
    <>
      <div className="section-title">HMRC exchange rates</div>
      <div className="panel-box">
        <p style={{ marginBottom: 12, color: 'var(--text-dimmed)', fontSize: 13 }}>
          HMRC publishes monthly exchange rates for converting foreign currency amounts. These rates are sourced from frankfurter.dev.
        </p>
        <DataTable
          columns={[
            { key: 'currency', label: 'Currency', width: '80px' },
            { key: 'rate', label: 'Rate (to GBP)', type: 'number', width: '120px' },
            { key: 'month', label: 'Month', width: '120px' },
          ]}
          data={[
            { currency: 'USD', rate: '0.7890', month: 'Mar 2026' },
            { currency: 'EUR', rate: '0.8560', month: 'Mar 2026' },
            { currency: 'CHF', rate: '0.8890', month: 'Mar 2026' },
            { currency: 'JPY', rate: '0.0052', month: 'Mar 2026' },
            { currency: 'AUD', rate: '0.5120', month: 'Mar 2026' },
            { currency: 'CAD', rate: '0.5780', month: 'Mar 2026' },
          ]}
          emptyMessage="No rates available"
        />
        <div className="form-actions" style={{ marginTop: 12 }}>
          <button className="btn btn-secondary">Download full rates</button>
        </div>
      </div>
    </>
  );

  const panels = {
    overview: renderOverview,
    'self-employment': renderSelfEmployment,
    'paye-summary': renderPayeSummary,
    'self-assessment': renderSelfAssessment,
    'hmrc-rates': renderHmrcRates,
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
      {loading && activePanel === 'overview' ? (
        <div className="loading">Loading tax data...</div>
      ) : (
        (panels[activePanel] || renderOverview)()
      )}
    </Layout>
  );
}
