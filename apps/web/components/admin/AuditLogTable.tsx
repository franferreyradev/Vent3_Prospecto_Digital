'use client';

import type { components } from '@vent3/contracts';
import Table, { ColumnDef } from '../ui/Table';

type AuditLog = components['schemas']['AuditLogResponse'];

interface AuditLogTableProps {
  eventos: AuditLog[];
  loading: boolean;
}

const columns: ColumnDef<AuditLog>[] = [
  {
    key: 'created_at',
    header: 'Fecha',
    render: (e) => new Date(e.created_at).toLocaleString('es-AR'),
  },
  {
    key: 'tabla_afectada',
    header: 'Tabla',
  },
  {
    key: 'accion',
    header: 'Acción',
  },
  {
    key: 'campo_modificado',
    header: 'Campo',
    render: (e) => e.campo_modificado ?? '—',
  },
  {
    key: 'valor_anterior',
    header: 'Anterior → Nuevo',
    render: (e) => `${e.valor_anterior ?? '—'} → ${e.valor_nuevo ?? '—'}`,
  },
  {
    key: 'usuario_id',
    header: 'Usuario',
  },
  {
    key: 'ip_origen',
    header: 'IP origen',
    render: (e) => e.ip_origen ?? '—',
  },
];

export default function AuditLogTable({ eventos, loading }: AuditLogTableProps) {
  return <Table<AuditLog> columns={columns} data={eventos} loading={loading} />;
}
