import React from 'react';

const MODULES = [
  { key: 'dashboard', label: 'Dashboard', hotkey: 'D', hotkeyIndex: 0 },
  { key: 'income', label: 'Income', hotkey: 'I', hotkeyIndex: 0 },
  { key: 'expenses', label: 'Expenses', hotkey: 'E', hotkeyIndex: 0 },
  { key: 'invoices', label: 'Invoices', hotkey: 'V', hotkeyIndex: 2 },
  { key: 'tax', label: 'Tax', hotkey: 'T', hotkeyIndex: 0 },
  { key: 'reports', label: 'Reports', hotkey: 'R', hotkeyIndex: 0 },
  { key: 'settings', label: 'Settings', hotkey: 'S', hotkeyIndex: 0 },
];

function renderLabel(label, hotkeyIndex) {
  const before = label.slice(0, hotkeyIndex);
  const char = label[hotkeyIndex];
  const after = label.slice(hotkeyIndex + 1);
  return (
    <>
      {before}
      <span className="hotkey">{char}</span>
      {after}
    </>
  );
}

export default function MenuBar({ activeModule, onModuleChange }) {
  return (
    <div className="menubar">
      {MODULES.map((m) => (
        <div
          key={m.key}
          className={`menubar-item${activeModule === m.key ? ' active' : ''}`}
          onClick={() => onModuleChange(m.key)}
        >
          {renderLabel(m.label, m.hotkeyIndex)}
        </div>
      ))}
    </div>
  );
}
