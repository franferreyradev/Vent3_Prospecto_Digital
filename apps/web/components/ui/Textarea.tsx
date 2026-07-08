'use client';

import { TextareaHTMLAttributes, useId } from 'react';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  error?: string;
  helperText?: string;
}

export default function Textarea({
  label,
  error,
  helperText,
  id,
  className = '',
  rows = 5,
  ...rest
}: TextareaProps) {
  const generatedId = useId();
  const textareaId = id ?? generatedId;

  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={textareaId} className="text-sm font-medium text-vent3-text-primary">
        {label}
      </label>
      <textarea
        id={textareaId}
        rows={rows}
        className={`rounded-md border bg-vent3-bg px-3 py-2 text-vent3-text-primary focus:outline-none focus:ring-2 focus:ring-vent3-primary ${
          error ? 'border-vent3-danger' : 'border-vent3-border'
        } ${className}`}
        aria-invalid={!!error}
        aria-describedby={error || helperText ? `${textareaId}-help` : undefined}
        {...rest}
      />
      {error ? (
        <span id={`${textareaId}-help`} className="text-sm text-vent3-danger">
          {error}
        </span>
      ) : helperText ? (
        <span id={`${textareaId}-help`} className="text-sm text-vent3-text-secondary">
          {helperText}
        </span>
      ) : null}
    </div>
  );
}
