'use client';

import type { components } from '@vent3/contracts';
import { useState } from 'react';
import { cambiarEstadoUsuario } from '../../lib/api-client';
import Badge from '../ui/Badge';
import Button from '../ui/Button';

type Usuario = components['schemas']['UsuarioResponse'];

interface UsuariosTableProps {
  usuarios: Usuario[];
  loading: boolean;
  usuarioActualId: string;
  onActualizado: (usuario: Usuario) => void;
}

export default function UsuariosTable({
  usuarios,
  loading,
  usuarioActualId,
  onActualizado,
}: UsuariosTableProps) {
  const [confirmacion, setConfirmacion] = useState<Usuario | null>(null);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState('');

  async function ejecutarCambioEstado(usuario: Usuario) {
    setGuardando(true);
    setError('');
    try {
      const actualizado = await cambiarEstadoUsuario(usuario.id, { activo: !usuario.activo });
      onActualizado(actualizado);
      setConfirmacion(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al cambiar el estado del usuario');
      setConfirmacion(null);
    } finally {
      setGuardando(false);
    }
  }

  return (
    <>
      {confirmacion && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-lg bg-vent3-bg p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-vent3-text-primary">
              {confirmacion.activo ? 'Desactivar usuario' : 'Reactivar usuario'}
            </h2>
            <p className="mt-2 text-sm text-vent3-text-secondary">
              {confirmacion.activo
                ? `${confirmacion.email} no va a poder iniciar sesión hasta que lo reactives.`
                : `${confirmacion.email} va a poder volver a iniciar sesión.`}
            </p>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={() => setConfirmacion(null)}>
                Cancelar
              </Button>
              <Button
                variant={confirmacion.activo ? 'danger' : 'primary'}
                size="sm"
                loading={guardando}
                onClick={() => void ejecutarCambioEstado(confirmacion)}
              >
                Confirmar
              </Button>
            </div>
          </div>
        </div>
      )}

      {error && <p className="mb-2 text-sm text-vent3-danger">{error}</p>}

      <table className="w-full border-collapse text-left">
        <thead>
          <tr className="border-b border-vent3-border">
            <th className="px-4 py-2 text-sm font-medium text-vent3-text-secondary">Email</th>
            <th className="px-4 py-2 text-sm font-medium text-vent3-text-secondary">Nombre</th>
            <th className="px-4 py-2 text-sm font-medium text-vent3-text-secondary">Rol</th>
            <th className="px-4 py-2 text-sm font-medium text-vent3-text-secondary">Estado</th>
            <th className="px-4 py-2 text-sm font-medium text-vent3-text-secondary">
              Último acceso
            </th>
            <th className="px-4 py-2 text-sm font-medium text-vent3-text-secondary" />
          </tr>
        </thead>
        <tbody>
          {loading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <tr key={i} className="border-b border-vent3-border">
                <td className="px-4 py-3" colSpan={6}>
                  <div className="h-4 w-full animate-pulse rounded bg-vent3-surface" />
                </td>
              </tr>
            ))
          ) : usuarios.length === 0 ? (
            <tr>
              <td colSpan={6} className="px-4 py-6 text-center text-sm text-vent3-text-secondary">
                Sin resultados
              </td>
            </tr>
          ) : (
            usuarios.map((usuario) => (
              <tr key={usuario.id} className="border-b border-vent3-border">
                <td className="px-4 py-3 text-sm text-vent3-text-primary">{usuario.email}</td>
                <td className="px-4 py-3 text-sm text-vent3-text-primary">{usuario.nombre}</td>
                <td className="px-4 py-3 text-sm text-vent3-text-secondary">{usuario.rol}</td>
                <td className="px-4 py-3">
                  <Badge
                    variant={usuario.activo ? 'success' : 'neutral'}
                    label={usuario.activo ? 'Activo' : 'Inactivo'}
                  />
                </td>
                <td className="px-4 py-3 text-sm text-vent3-text-secondary">
                  {usuario.ultimo_acceso
                    ? new Date(usuario.ultimo_acceso).toLocaleString('es-AR')
                    : '—'}
                </td>
                <td className="px-4 py-3">
                  {usuario.id === usuarioActualId ? (
                    <span className="text-xs text-vent3-text-secondary">Vos</span>
                  ) : (
                    <Button
                      variant={usuario.activo ? 'danger' : 'secondary'}
                      size="sm"
                      onClick={() => setConfirmacion(usuario)}
                    >
                      {usuario.activo ? 'Desactivar' : 'Reactivar'}
                    </Button>
                  )}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </>
  );
}
