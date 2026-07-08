'use client';

import type { components } from '@vent3/contracts';
import { useEffect, useState } from 'react';
import { listarAuditLog } from '../../../lib/api-client';
import AuditLogTable from '../../../components/admin/AuditLogTable';
import Input from '../../../components/ui/Input';
import Button from '../../../components/ui/Button';

type AuditLog = components['schemas']['AuditLogResponse'];

const LIMIT = 50;

export default function AuditoriaPage() {
  const [eventos, setEventos] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [tabla, setTabla] = useState('');
  const [usuarioId, setUsuarioId] = useState('');
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setPage(1);
  }, [tabla, usuarioId, desde, hasta]);

  useEffect(() => {
    setLoading(true);
    const timeout = setTimeout(() => {
      listarAuditLog({
        tabla: tabla || undefined,
        usuario_id: usuarioId || undefined,
        desde: desde || undefined,
        hasta: hasta || undefined,
        page,
        limit: LIMIT,
      })
        .then((res) => {
          setEventos(res.data);
          setTotal(res.total);
        })
        .finally(() => setLoading(false));
    }, 400);

    return () => clearTimeout(timeout);
  }, [page, tabla, usuarioId, desde, hasta]);

  const totalPaginas = Math.ceil(total / LIMIT) || 1;

  return (
    <div className="min-h-screen bg-vent3-bg px-8 py-8">
      <h1 className="mb-6 text-xl font-semibold text-vent3-text-primary">Auditoría</h1>

      <div className="mb-6 flex flex-wrap gap-4">
        <Input
          label="Tabla afectada"
          type="text"
          value={tabla}
          onChange={(e) => setTabla(e.target.value)}
        />
        <Input
          label="Usuario (UUID)"
          type="text"
          value={usuarioId}
          onChange={(e) => setUsuarioId(e.target.value)}
        />
        <Input
          label="Desde"
          type="date"
          value={desde}
          onChange={(e) => setDesde(e.target.value)}
        />
        <Input
          label="Hasta"
          type="date"
          value={hasta}
          onChange={(e) => setHasta(e.target.value)}
        />
      </div>

      <AuditLogTable eventos={eventos} loading={loading} />

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
