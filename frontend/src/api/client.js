import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

// --- Transactions ---
export async function getTransactions(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') params.append(k, v);
  });
  const { data } = await api.get(`/transactions?${params}`);
  return data;
}

export async function createTransaction(txData) {
  const { data } = await api.post('/transactions', txData);
  return data;
}

export async function updateTransaction(id, txData) {
  const { data } = await api.put(`/transactions/${id}`, txData);
  return data;
}

export async function deleteTransaction(id) {
  const { data } = await api.delete(`/transactions/${id}`);
  return data;
}

// --- Invoices ---
export async function getInvoices() {
  const { data } = await api.get('/invoices');
  return data;
}

export async function createInvoice(invoiceData) {
  const { data } = await api.post('/invoices', invoiceData);
  return data;
}

export async function updateInvoiceStatus(id, status) {
  const { data } = await api.patch(`/invoices/${id}/status`, { status });
  return data;
}

export async function getInvoicePdf(id) {
  const { data } = await api.get(`/invoices/${id}/pdf`, { responseType: 'blob' });
  return data;
}

// --- PAYE ---
export async function getPAYEEntries() {
  const { data } = await api.get('/paye');
  return data;
}

export async function createPAYEEntry(entryData) {
  const { data } = await api.post('/paye', entryData);
  return data;
}

export async function getPAYESummary() {
  const { data } = await api.get('/paye/summary');
  return data;
}

// --- Tax ---
export async function getTaxSummary() {
  const { data } = await api.get('/tax/summary');
  return data;
}

export async function getSelfAssessment() {
  const { data } = await api.get('/tax/self-assessment');
  return data;
}

// --- Reports ---
export async function getReports(type, params = {}) {
  const query = new URLSearchParams(params);
  const { data } = await api.get(`/reports/${type}?${query}`);
  return data;
}

// --- Categories ---
export async function getCategories() {
  const { data } = await api.get('/categories');
  return data;
}

export async function createCategory(catData) {
  const { data } = await api.post('/categories', catData);
  return data;
}

// --- Settings ---
export async function getSettings(key) {
  const { data } = await api.get(`/settings/${key}`);
  return data;
}

export async function updateSettings(key, value) {
  const { data } = await api.put(`/settings/${key}`, value);
  return data;
}

// --- Exchange Rates ---
export async function getExchangeRate(currency, date) {
  const { data } = await api.get(`/exchange-rate?currency=${currency}&date=${date}`);
  return data;
}

// --- AI / Scanning ---
export async function scanReceipt(file) {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post('/scan/receipt', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function scanInvoice(file) {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post('/scan/invoice', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function suggestCategory(txData) {
  const { data } = await api.post('/ai/suggest-category', txData);
  return data;
}

// --- Import ---
export async function getImportProfiles() {
  const { data } = await api.get('/import/profiles');
  return data;
}

export async function uploadImport(file, profileName) {
  const form = new FormData();
  form.append('file', file);
  form.append('profile', profileName);
  const { data } = await api.post('/import/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export default api;
