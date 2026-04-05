import React from 'react';

export default function Sidebar({ items = [], activeItem, onItemChange }) {
  return (
    <div className="sidebar">
      {items.map((item, idx) => {
        if (item.divider) {
          return <div key={`div-${idx}`} className="sidebar-divider" />;
        }
        return (
          <div
            key={item.key}
            className={`sidebar-item${activeItem === item.key ? ' active' : ''}`}
            onClick={() => onItemChange(item.key)}
          >
            <span>{item.label}</span>
            {item.shortcut && <span className="shortcut">{item.shortcut}</span>}
          </div>
        );
      })}
    </div>
  );
}
