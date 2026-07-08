'use client';

import type { components } from '@vent3/contracts';
import Table, { ColumnDef } from '../ui/Table';
import Badge from '../ui/Badge';

type Producto = components['schemas']['ProductoListResponse'];

interface ProductTableProps {
  productos: Producto[];
  loading: boolean;
  onRowClick: (producto: Producto) => void;
}

const columns: ColumnDef<Producto>[] = [
  {
    key: 'codigo_interno',
    header: 'Código interno',
    render: (p) => p.codigo_interno ?? '—',
  },
  {
    key: 'nombre_comercial',
    header: 'Nombre',
  },
  {
    key: 'forma_farmaceutica',
    header: 'Presentación',
    render: (p) => `${p.forma_farmaceutica} · ${p.presentacion_cantidad}`,
  },
  {
    key: 'estado',
    header: 'Estado',
    render: (p) => (
      <Badge
        variant={p.estado === 'activo' ? 'success' : 'neutral'}
        label={p.estado === 'activo' ? 'Activo' : 'Inactivo'}
      />
    ),
  },
  {
    key: 'tiene_prospecto',
    header: 'Prospecto',
    render: (p) => (
      <Badge
        variant={p.tiene_prospecto ? 'success' : 'neutral'}
        label={p.tiene_prospecto ? 'Sí' : 'No'}
      />
    ),
  },
];

export default function ProductTable({ productos, loading, onRowClick }: ProductTableProps) {
  return (
    <Table<Producto>
      columns={columns}
      data={productos}
      loading={loading}
      onRowClick={onRowClick}
    />
  );
}
