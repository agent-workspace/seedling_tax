import React from 'react';

export default function SummaryCard({ label, value, variant = 'neutral' }) {
  return (
    <div className={`summary-card ${variant}`}>
      <div className="summary-card-label">{label}</div>
      <div className="summary-card-value">{value}</div>
    </div>
  );
}
