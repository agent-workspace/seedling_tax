import React from 'react';

export default function DataTable({ columns = [], data = [], onRowClick, emptyMessage = 'No data yet' }) {
  if (!data.length) {
    return <div className="empty-state">{emptyMessage}</div>;
  }

  return (
    <div className="data-table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key} style={col.width ? { width: col.width } : undefined}>
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr
              key={row.id || idx}
              className={onRowClick ? 'clickable' : ''}
              onClick={() => onRowClick && onRowClick(row, idx)}
            >
              {columns.map((col) => {
                let className = '';
                if (col.type === 'number' || col.type === 'currency') className = 'col-number';
                if (col.type === 'date') className = 'col-date';
                if (col.type === 'status') className = 'col-status';

                let content = row[col.key];

                if (col.type === 'currency' && content !== undefined && content !== null) {
                  const num = parseFloat(content);
                  content = isNaN(num) ? content : num.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                }

                if (col.type === 'status' && content) {
                  const badgeClass = `badge badge-${content.toLowerCase().replace(/\s+/g, '-')}`;
                  content = <span className={badgeClass}>{content}</span>;
                }

                if (col.type === 'receipt') {
                  content = <span className={`receipt-indicator${content ? '' : ' none'}`} />;
                }

                if (col.render) {
                  content = col.render(row, idx);
                }

                return (
                  <td key={col.key} className={className}>
                    {content}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
