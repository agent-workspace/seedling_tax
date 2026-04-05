import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';
import Layout from '../components/Layout';
import SummaryCard from '../components/SummaryCard';
import FormInput from '../components/FormInput';
import useKeyboard from '../hooks/useKeyboard';
import { getReports } from '../api/client';

const SIDEBAR_ITEMS = [
  { key: 'pnl', label: 'Profit & Loss', shortcut: '1' },
  { key: 'expense-breakdown', label: 'Expense breakdown', shortcut: '2' },
  { key: 'income-source', label: 'Income by source', shortcut: '3' },
  { key: 'tax-overview', label: 'Tax overview', shortcut: '4' },
  { key: 'monthly-trends', label: 'Monthly trends', shortcut: '5' },
  { key: 'cash-flow', label: 'Cash flow', shortcut: '6' },
];

const STATUS_HINTS = [
  { key: 'Alt+R', label: 'Reports' },
  { key: '1-6', label: 'Navigate' },
  { key: '?', label: 'Shortcuts' },
];

const DATE_RANGES = [
  { value: 'this-month', label: 'This month' },
  { value: 'this-quarter', label: 'This quarter' },
  { value: 'this-tax-year', label: 'This tax year' },
  { value: 'last-tax-year', label: 'Last tax year' },
  { value: 'custom', label: 'Custom' },
];

const COLORS = ['#5DCAA5', '#EF9F27', '#FAC775', '#B4B2A9', '#0F6E56', '#7A7A78', '#F1EFE8', '#c0392b'];

const MOCK_MONTHLY = [
  { month: 'Apr', income: 3200, expenses: 1400 },
  { month: 'May', income: 4100, expenses: 1800 },
  { month: 'Jun', income: 3800, expenses: 2100 },
  { month: 'Jul', income: 5200, expenses: 1900 },
  { month: 'Aug', income: 4600, expenses: 2300 },
  { month: 'Sep', income: 3900, expenses: 1700 },
  { month: 'Oct', income: 4800, expenses: 2000 },
  { month: 'Nov', income: 5100, expenses: 2400 },
  { month: 'Dec', income: 3700, expenses: 1600 },
  { month: 'Jan', income: 4400, expenses: 1900 },
  { month: 'Feb', income: 4900, expenses: 2200 },
  { month: 'Mar', income: 5300, expenses: 2100 },
];

const MOCK_EXPENSE_CATS = [
  { name: 'Office costs', value: 2400 },
  { name: 'Travel', value: 3200 },
  { name: 'Phone & internet', value: 1800 },
  { name: 'Professional fees', value: 2600 },
  { name: 'Insurance', value: 1200 },
  { name: 'Other', value: 900 },
];

const MOCK_INCOME_SRC = [
  { name: 'Self-employment', value: 38000 },
  { name: 'PAYE', value: 12000 },
  { name: 'Freelance', value: 8200 },
  { name: 'Other', value: 1400 },
];

const MOCK_CASHFLOW = MOCK_MONTHLY.map((m) => ({
  month: m.month,
  net: m.income - m.expenses,
  cumulative: 0,
}));
let cum = 0;
MOCK_CASHFLOW.forEach((m) => {
  cum += m.net;
  m.cumulative = cum;
});

const tooltipStyle = {
  backgroundColor: '#2C2C2A',
  border: '1px solid rgba(255,255,255,0.15)',
  borderRadius: 4,
  fontFamily: "'IBM Plex Mono', monospace",
  fontSize: 12,
  color: '#F1EFE8',
};

export default function Reports({ activeModule, onModuleChange }) {
  const [activePanel, setActivePanel] = useState('pnl');
  const [dateRange, setDateRange] = useState('this-tax-year');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);

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
      setLoading(true);
      try {
        const data = await getReports(activePanel, { range: dateRange });
        if (!cancelled) setReportData(data);
      } catch {
        if (!cancelled) setReportData(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [activePanel, dateRange]);

  const totalIncome = MOCK_MONTHLY.reduce((s, m) => s + m.income, 0);
  const totalExpenses = MOCK_MONTHLY.reduce((s, m) => s + m.expenses, 0);
  const fmt = (n) => `\u00a3${(n || 0).toLocaleString('en-GB', { minimumFractionDigits: 2 })}`;

  const dateFilter = (
    <div className="date-filter">
      <label>Period:</label>
      <FormInput
        type="select"
        value={dateRange}
        onChange={setDateRange}
        options={DATE_RANGES}
        size="medium"
      />
    </div>
  );

  const renderPnL = () => (
    <>
      <div className="section-title">Profit & Loss</div>
      {dateFilter}
      <div className="summary-cards">
        <SummaryCard label="Total Income" value={fmt(totalIncome)} variant="good" />
        <SummaryCard label="Total Expenses" value={fmt(totalExpenses)} variant="warn" />
        <SummaryCard label="Net Profit" value={fmt(totalIncome - totalExpenses)} variant="good" />
      </div>
      <div className="chart-container">
        <div className="chart-title">Income vs Expenses by month</div>
        <ResponsiveContainer width="100%" height={320}>
          <BarChart data={MOCK_MONTHLY}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
            <XAxis dataKey="month" tick={{ fill: '#B4B2A9', fontSize: 12, fontFamily: "'IBM Plex Mono'" }} />
            <YAxis tick={{ fill: '#B4B2A9', fontSize: 12, fontFamily: "'IBM Plex Mono'" }} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ fontFamily: "'IBM Plex Mono'", fontSize: 12 }} />
            <Bar dataKey="income" fill="#5DCAA5" name="Income" radius={[2, 2, 0, 0]} />
            <Bar dataKey="expenses" fill="#EF9F27" name="Expenses" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  );

  const renderExpenseBreakdown = () => (
    <>
      <div className="section-title">Expense breakdown</div>
      {dateFilter}
      <div className="chart-container">
        <div className="chart-title">By category</div>
        <ResponsiveContainer width="100%" height={360}>
          <PieChart>
            <Pie
              data={MOCK_EXPENSE_CATS}
              cx="50%"
              cy="50%"
              innerRadius={70}
              outerRadius={130}
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              labelLine={{ stroke: '#B4B2A9' }}
            >
              {MOCK_EXPENSE_CATS.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={tooltipStyle} formatter={(v) => fmt(v)} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </>
  );

  const renderIncomeSource = () => (
    <>
      <div className="section-title">Income by source</div>
      {dateFilter}
      <div className="chart-container">
        <div className="chart-title">By source</div>
        <ResponsiveContainer width="100%" height={360}>
          <PieChart>
            <Pie
              data={MOCK_INCOME_SRC}
              cx="50%"
              cy="50%"
              innerRadius={70}
              outerRadius={130}
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              labelLine={{ stroke: '#B4B2A9' }}
            >
              {MOCK_INCOME_SRC.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={tooltipStyle} formatter={(v) => fmt(v)} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </>
  );

  const renderTaxOverview = () => {
    const taxableProfit = totalIncome - totalExpenses;
    const incomeTax = Math.max(0, (taxableProfit - 12570) * 0.2);
    const ni = Math.max(0, (taxableProfit - 12570) * 0.06);
    const total = incomeTax + ni;
    const rate = totalIncome > 0 ? ((total / totalIncome) * 100).toFixed(1) : '0.0';

    return (
      <>
        <div className="section-title">Tax overview</div>
        {dateFilter}
        <div className="summary-cards">
          <SummaryCard label="Taxable Profit" value={fmt(taxableProfit)} variant="neutral" />
          <SummaryCard label="Income Tax" value={fmt(incomeTax)} variant="warn" />
          <SummaryCard label="NI" value={fmt(ni)} variant="warn" />
          <SummaryCard label="Total Tax" value={fmt(total)} variant="warn" />
          <SummaryCard label="Effective Rate" value={`${rate}%`} variant="neutral" />
        </div>
      </>
    );
  };

  const renderMonthlyTrends = () => (
    <>
      <div className="section-title">Monthly trends</div>
      {dateFilter}
      <div className="chart-container">
        <div className="chart-title">Income vs Expenses over time</div>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={MOCK_MONTHLY}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
            <XAxis dataKey="month" tick={{ fill: '#B4B2A9', fontSize: 12, fontFamily: "'IBM Plex Mono'" }} />
            <YAxis tick={{ fill: '#B4B2A9', fontSize: 12, fontFamily: "'IBM Plex Mono'" }} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ fontFamily: "'IBM Plex Mono'", fontSize: 12 }} />
            <Line type="monotone" dataKey="income" stroke="#5DCAA5" strokeWidth={2} dot={{ r: 4, fill: '#5DCAA5' }} name="Income" />
            <Line type="monotone" dataKey="expenses" stroke="#EF9F27" strokeWidth={2} dot={{ r: 4, fill: '#EF9F27' }} name="Expenses" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </>
  );

  const renderCashFlow = () => (
    <>
      <div className="section-title">Cash flow</div>
      {dateFilter}
      <div className="chart-container">
        <div className="chart-title">Net income over time</div>
        <ResponsiveContainer width="100%" height={320}>
          <AreaChart data={MOCK_CASHFLOW}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
            <XAxis dataKey="month" tick={{ fill: '#B4B2A9', fontSize: 12, fontFamily: "'IBM Plex Mono'" }} />
            <YAxis tick={{ fill: '#B4B2A9', fontSize: 12, fontFamily: "'IBM Plex Mono'" }} />
            <Tooltip contentStyle={tooltipStyle} />
            <Legend wrapperStyle={{ fontFamily: "'IBM Plex Mono'", fontSize: 12 }} />
            <Area type="monotone" dataKey="cumulative" stroke="#5DCAA5" fill="rgba(93,202,165,0.15)" strokeWidth={2} name="Cumulative" />
            <Area type="monotone" dataKey="net" stroke="#0F6E56" fill="rgba(15,110,86,0.1)" strokeWidth={1} name="Monthly net" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </>
  );

  const panels = {
    pnl: renderPnL,
    'expense-breakdown': renderExpenseBreakdown,
    'income-source': renderIncomeSource,
    'tax-overview': renderTaxOverview,
    'monthly-trends': renderMonthlyTrends,
    'cash-flow': renderCashFlow,
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
      {(panels[activePanel] || renderPnL)()}
    </Layout>
  );
}
