import React from 'react';

export default function FormInput({
  label,
  type = 'text',
  value,
  onChange,
  options,
  placeholder,
  size = 'full',
  name,
  min,
  max,
  step,
  rows,
  disabled,
}) {
  const sizeClass = size === 'small' ? 'small' : size === 'medium' ? 'medium' : 'full';

  const handleChange = (e) => {
    if (onChange) onChange(e.target.value, e);
  };

  let input;
  if (type === 'select') {
    input = (
      <select className="form-select" value={value || ''} onChange={handleChange} name={name} disabled={disabled}>
        {placeholder && <option value="">{placeholder}</option>}
        {(options || []).map((opt) => {
          const val = typeof opt === 'string' ? opt : opt.value;
          const lbl = typeof opt === 'string' ? opt : opt.label;
          return (
            <option key={val} value={val}>
              {lbl}
            </option>
          );
        })}
      </select>
    );
  } else if (type === 'textarea') {
    input = (
      <textarea
        className="form-textarea"
        value={value || ''}
        onChange={handleChange}
        placeholder={placeholder}
        name={name}
        rows={rows || 4}
        disabled={disabled}
      />
    );
  } else {
    input = (
      <input
        className="form-input"
        type={type}
        value={value || ''}
        onChange={handleChange}
        placeholder={placeholder}
        name={name}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
      />
    );
  }

  return (
    <div className={`form-group ${sizeClass}`}>
      {label && <label className="form-label">{label}</label>}
      {input}
    </div>
  );
}
