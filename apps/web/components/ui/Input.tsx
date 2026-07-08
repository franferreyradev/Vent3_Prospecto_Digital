'use client';

import { InputHTMLAttributes, useId } from 'react';

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string;
  type: 'text' | 'email' | 'password' | 'file' | 'date';
  error?: string;
  helperText?: string;
}

export default function Input({
  label,
  type,
  error,
  helperText,
  id,
  className = '',
  ...rest
}: InputProps) {
  const generatedId = useId();
  const inputId = id ?? generatedId;

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={inputId} className="text-sm font-medium text-vent3-text-primary">
        {label}
      </label>
      <input
        id={inputId}
        type={type}
        className={`rounded-md border bg-vent3-bg px-3 py-2 text-vent3-text-primary focus:outline-none focus:ring-2 focus:ring-vent3-primary ${
          error ? 'border-vent3-danger' : 'border-vent3-border'
        } ${className}`}
        aria-invalid={!!error}
        aria-describedby={error || helperText ? `${inputId}-help` : undefined}
        {...rest}
      />
      {error ? (
        <span id={`${inputId}-help`} className="text-sm text-vent3-danger">
          {error}
        </span>
      ) : helperText ? (
        <span id={`${inputId}-help`} className="text-sm text-vent3-text-secondary">
          {helperText}
        </span>
      ) : null}
    </div>
  );
}
