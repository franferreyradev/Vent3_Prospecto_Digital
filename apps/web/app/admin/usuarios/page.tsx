'use client';

import type { components } from '@vent3/contracts';
import { useEffect, useState } from 'react';
import { getMe, listarUsuarios } from '../../../lib/api-client';
import UsuariosTable from '../../../components/admin/UsuariosTable';
import InvitacionModal from '../../../components/admin/InvitacionModal';
import Input from '../../../components/ui/Input';
import Select from '../../../components/ui/Select';
import Button from '../../../components/ui/Button';

type Usuario = components['schemas']['UsuarioResponse'];

const LIMIT = 50;

export default function UsuariosPage() {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [rol, setRol] = useState('');
  const [activo, setActivo] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [usuarioActualId, setUsuarioActualId] = useState('');
  const [mostrarInvitacion, setMostrarInvitacion] = useState(false);

  useEffect(() => {
    getMe().then((me) => setUsuarioActualId(me.id));
  }, []);

  useEffect(() => {
    setPage(1);
  }, [rol, activo, search]);

  function recargar() {
    setLoading(true);
    return listarUsuarios({
      rol: rol || undefined,
      activo: activo || undefined,
      search: search || undefined,
      page,
      limit: LIMIT,
    })
      .then((res) => {
        setUsuarios(res.data);
        setTotal(res.total);
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    const timeout = setTimeout(() => {
      void recargar();
    }, 400);

    return () => clearTimeout(timeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, rol, activo, search]);

  function handleActualizado(usuario: Usuario) {
    setUsuarios((prev) => prev.map((u) => (u.id === usuario.id ? usuario : u)));
  }

  const totalPaginas = Math.ceil(total / LIMIT) || 1;

  return (
    <div className="min-h-screen bg-vent3-bg px-8 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-vent3-text-primary">Usuarios</h1>
        <Button variant="primary" size="sm" onClick={() => setMostrarInvitacion(true)}>
          Nueva invitación
        </Button>
      </div>

      {mostrarInvitacion && (
        <InvitacionModal
          onClose={() => {
            setMostrarInvitacion(false);
            void recargar();
          }}
        />
      )}

      <div className="mb-6 flex flex-wrap gap-4">
        <Input
          label="Buscar"
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Email o nombre"
        />
        <Select
          label="Rol"
          value={rol}
          onChange={setRol}
          options={[
            { value: '', label: 'Todos' },
            { value: 'admin', label: 'Admin' },
            { value: 'editor', label: 'Editor' },
            { value: 'lector', label: 'Lector' },
          ]}
        />
        <Select
          label="Estado"
          value={activo}
          onChange={setActivo}
          options={[
            { value: '', label: 'Todos' },
            { value: 'true', label: 'Activo' },
            { value: 'false', label: 'Inactivo' },
          ]}
        />
      </div>

      <UsuariosTable
        usuarios={usuarios}
        loading={loading}
        usuarioActualId={usuarioActualId}
        onActualizado={handleActualizado}
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
