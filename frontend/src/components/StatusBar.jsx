import React from 'react';

export default function StatusBar({ hints = [] }) {
  return (
    <div className="statusbar">
      <div className="statusbar-hints">
        {hints.map((h, i) => (
          <span key={i} className="statusbar-hint">
            <span className="hint-key">{h.key}</span>
            {h.label}
          </span>
        ))}
      </div>
      <div className="statusbar-right">
        seedling tax v0.1 &middot; GBP base &middot; frankfurter.dev
      </div>
    </div>
  );
}
