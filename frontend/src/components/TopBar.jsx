import React from 'react';

export default function TopBar({ taxYear = '2025/26', entityType = 'Sole Trader', userName = 'User' }) {
  return (
    <div className="topbar">
      <span className="topbar-logo">seedling tax</span>
      <div className="topbar-context">
        <span>Tax year: {taxYear}</span>
        <span>{entityType}</span>
        <span>{userName}</span>
      </div>
    </div>
  );
}
