'use client';

import { ReactNode } from 'react';

export interface ColumnDef<T> {
  key: keyof T;
  header: string;
  render?: (row: T) => ReactNode;
}

interface TableProps<T> {
  columns: ColumnDef<T>[];
  data: T[];
  loading?: boolean;
  onRowClick?: (row: T) => void;
}

export default function Table<T extends { id?: string | number }>({
  columns,
  data,
  loading = false,
  onRowClick,
}: TableProps<T>) {
  return (
    <table className="w-full border-collapse text-left">
      <thead>
        <tr className="border-b border-vent3-border">
          {columns.map((column) => (
            <th
              key={String(column.key)}
              className="px-4 py-2 text-sm font-medium text-vent3-text-secondary"
            >
              {column.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {loading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <tr key={i} className="border-b border-vent3-border">
              {columns.map((column) => (
                <td key={String(column.key)} className="px-4 py-3">
                  <div className="h-4 w-full animate-pulse rounded bg-vent3-surface" />
                </td>
              ))}
            </tr>
          ))
        ) : data.length === 0 ? (
          <tr>
            <td
              colSpan={columns.length}
              className="px-4 py-6 text-center text-sm text-vent3-text-secondary"
            >
              Sin resultados
            </td>
          </tr>
        ) : (
          data.map((row, i) => (
            <tr
              key={row.id ?? i}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={`border-b border-vent3-border ${
                onRowClick ? 'cursor-pointer hover:bg-vent3-surface' : ''
              }`}
            >
              {columns.map((column) => (
                <td key={String(column.key)} className="px-4 py-3 text-vent3-text-primary">
                  {column.render ? column.render(row) : String(row[column.key] ?? '')}
                </td>
              ))}
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}
