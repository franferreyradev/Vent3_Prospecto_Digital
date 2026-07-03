'use client';

import { useEffect, useState } from 'react';

type ToastType = 'success' | 'error' | 'info';

interface ToastProps {
  type: ToastType;
  message: string;
  duration?: number;
}

const typeStyles: Record<ToastType, string> = {
  success: 'bg-vent3-success text-vent3-bg',
  error: 'bg-vent3-danger text-vent3-bg',
  info: 'bg-vent3-primary text-vent3-bg',
};

export default function Toast({ type, message, duration = 4000 }: ToastProps) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(false), duration);
    return () => clearTimeout(timer);
  }, [duration]);

  if (!visible) return null;

  return (
    <div
      role="status"
      className={`rounded-md px-4 py-3 text-sm font-medium shadow-md ${typeStyles[type]}`}
    >
      {message}
    </div>
  );
}
