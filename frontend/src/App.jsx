import React, { useState, useCallback } from 'react';
import { Routes, Route, useNavigate, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Income from './pages/Income';
import Expenses from './pages/Expenses';
import Invoices from './pages/Invoices';
import Tax from './pages/Tax';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import useKeyboard from './hooks/useKeyboard';

const MODULE_KEYS = {
  d: 'dashboard',
  i: 'income',
  e: 'expenses',
  v: 'invoices',
  t: 'tax',
  r: 'reports',
  s: 'settings',
};

const MODULE_ROUTES = {
  dashboard: '/',
  income: '/income',
  expenses: '/expenses',
  invoices: '/invoices',
  tax: '/tax',
  reports: '/reports',
  settings: '/settings',
};

export default function App() {
  const [activeModule, setActiveModule] = useState('dashboard');
  const navigate = useNavigate();

  const handleModuleChange = useCallback(
    (mod) => {
      setActiveModule(mod);
      navigate(MODULE_ROUTES[mod]);
    },
    [navigate]
  );

  useKeyboard({
    onAltKey: (key) => {
      const mod = MODULE_KEYS[key];
      if (mod) handleModuleChange(mod);
    },
  });

  const renderPage = (Page, moduleName) => (
    <Page activeModule={moduleName} onModuleChange={handleModuleChange} />
  );

  return (
    <Routes>
      <Route path="/" element={renderPage(Dashboard, 'dashboard')} />
      <Route path="/income" element={renderPage(Income, 'income')} />
      <Route path="/expenses" element={renderPage(Expenses, 'expenses')} />
      <Route path="/invoices" element={renderPage(Invoices, 'invoices')} />
      <Route path="/tax" element={renderPage(Tax, 'tax')} />
      <Route path="/reports" element={renderPage(Reports, 'reports')} />
      <Route path="/settings" element={renderPage(Settings, 'settings')} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
