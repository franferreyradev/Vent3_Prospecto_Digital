'use client';

import { useId } from 'react';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  label: string;
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  error?: string;
}

export default function Select({ label, options, value, onChange, error }: SelectProps) {
  const selectId = useId();

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={selectId} className="text-sm font-medium text-vent3-text-primary">
        {label}
      </label>
      <select
        id={selectId}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`rounded-md border bg-vent3-bg px-3 py-2 text-vent3-text-primary focus:outline-none focus:ring-2 focus:ring-vent3-primary ${
          error ? 'border-vent3-danger' : 'border-vent3-border'
        }`}
        aria-invalid={!!error}
        aria-describedby={error ? `${selectId}-error` : undefined}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && (
        <span id={`${selectId}-error`} className="text-sm text-vent3-danger">
          {error}
        </span>
      )}
    </div>
  );
}
