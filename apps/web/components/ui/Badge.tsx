type BadgeVariant = 'success' | 'warning' | 'danger' | 'neutral';

interface BadgeProps {
  variant: BadgeVariant;
  label: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  success: 'bg-vent3-success/10 text-vent3-success',
  warning: 'bg-vent3-warning/10 text-vent3-warning',
  danger: 'bg-vent3-danger/10 text-vent3-danger',
  neutral: 'bg-vent3-surface text-vent3-text-secondary border border-vent3-border',
};

export default function Badge({ variant, label }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium ${variantStyles[variant]}`}
    >
      {label}
    </span>
  );
}
