'use client';

import type { components } from '@vent3/contracts';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { listarProductos } from '../../lib/api-client';
import ProductTable from '../../components/admin/ProductTable';
import Select from '../../components/ui/Select';
import Input from '../../components/ui/Input';
import Button from '../../components/ui/Button';

type Producto = components['schemas']['ProductoListResponse'];

const LIMIT = 50;

export default function AdminDashboardPage() {
  const router = useRouter();
  const [productos, setProductos] = useState<Producto[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [filtroEstado, setFiltroEstado] = useState('');
  const [filtroCanal, setFiltroCanal] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setPage(1);
  }, [filtroEstado, filtroCanal, search]);

  useEffect(() => {
    setLoading(true);
    const timeout = setTimeout(() => {
      listarProductos({
        estado: filtroEstado || undefined,
        canal: filtroCanal || undefined,
        search: search || undefined,
        page,
        limit: LIMIT,
      })
        .then((res) => {
          setProductos(res.data);
          setTotal(res.total);
        })
        .finally(() => setLoading(false));
    }, 400);

    return () => clearTimeout(timeout);
  }, [page, filtroEstado, filtroCanal, search]);

  const totalPaginas = Math.ceil(total / LIMIT) || 1;

  return (
    <div className="min-h-screen bg-vent3-bg px-8 py-8">
      <h1 className="mb-6 text-xl font-semibold text-vent3-text-primary">Productos</h1>

      <div className="mb-6 flex flex-wrap gap-4">
        <Select
          label="Estado"
          value={filtroEstado}
          onChange={setFiltroEstado}
          options={[
            { value: '', label: 'Todos' },
            { value: 'activo', label: 'Activo' },
            { value: 'inactivo', label: 'Inactivo' },
          ]}
        />
        <Select
          label="Canal"
          value={filtroCanal}
          onChange={setFiltroCanal}
          options={[
            { value: '', label: 'Todos' },
            { value: 'farmacia', label: 'Farmacia' },
            { value: 'licitacion', label: 'Licitación' },
          ]}
        />
        <Input
          label="Buscar por nombre"
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <ProductTable
        productos={productos}
        loading={loading}
        onRowClick={(producto) => router.push(`/admin/productos/${producto.id}`)}
      />

      <div className="mt-4 flex items-center justify-between">
        <span className="text-sm text-vent3-text-secondary">
          Página {page} de {totalPaginas}
        </span>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Anterior
          </Button>
          <Button
            variant="secondary"
            size="sm"
            disabled={page >= totalPaginas}
            onClick={() => setPage((p) => p + 1)}
          >
            Siguiente
          </Button>
        </div>
      </div>
    </div>
  );
}
