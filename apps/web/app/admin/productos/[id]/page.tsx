'use client';

import type { components } from '@vent3/contracts';
import { useCallback, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import {
  obtenerProducto,
  cambiarEstadoProducto,
  listarProspectos,
  activarProspecto,
  obtenerUrlDescargaProspecto,
} from '../../../../lib/api-client';
import GtinTable from '../../../../components/admin/GtinTable';
import UploadProspecto from '../../../../components/admin/UploadProspecto';
import Badge from '../../../../components/ui/Badge';
import Button from '../../../../components/ui/Button';
import Toast from '../../../../components/ui/Toast';

type Producto = components['schemas']['ProductoDetalleResponse'];
type Prospecto = components['schemas']['ProspectoResponse'];
type GtinRegistro = components['schemas']['GtinRegistroResponse'];

const ESTADO_VIGENCIA_BADGE: Record<string, { variant: 'success' | 'warning' | 'neutral'; label: string }> = {
  vigente: { variant: 'success', label: 'Vigente' },
  en_revision: { variant: 'warning', label: 'En revisión' },
  reemplazado: { variant: 'neutral', label: 'Reemplazado' },
};

export default function ProductoDetallePage() {
  const params = useParams<{ id: string }>();
  const productoId = params.id;

  const [producto, setProducto] = useState<Producto | null>(null);
  const [prospectos, setProspectos] = useState<Prospecto[]>([]);
  const [loading, setLoading] = useState(true);
  const [mostrarUpload, setMostrarUpload] = useState(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const cargarDatos = useCallback(async () => {
    setLoading(true);
    try {
      const [productoRes, prospectosRes] = await Promise.all([
        obtenerProducto(productoId),
        listarProspectos({ producto_id: productoId, limit: 100 }),
      ]);
      setProducto(productoRes);
      setProspectos(prospectosRes.data);
    } finally {
      setLoading(false);
    }
  }, [productoId]);

  useEffect(() => {
    cargarDatos();
  }, [cargarDatos]);

  async function handleCambiarEstado() {
    if (!producto) return;
    const nuevoEstado = producto.estado === 'activo' ? 'inactivo' : 'activo';
    try {
      const actualizado = await cambiarEstadoProducto(productoId, { estado: nuevoEstado });
      setProducto(actualizado);
      setToast({ type: 'success', message: `Producto ${nuevoEstado === 'activo' ? 'activado' : 'desactivado'}` });
    } catch (err) {
      setToast({ type: 'error', message: err instanceof Error ? err.message : 'Error al cambiar el estado' });
    }
  }

  async function handleSubido(prospectoId: string) {
    setMostrarUpload(false);
    setToast({ type: 'success', message: 'Prospecto subido correctamente' });
    await cargarDatos();

    if (window.confirm('¿Activar este prospecto ahora?')) {
      await handleActivar(prospectoId);
    }
  }

  async function handleActivar(prospectoId: string) {
    try {
      await activarProspecto(prospectoId, productoId);
      setToast({ type: 'success', message: 'Prospecto activado' });
      await cargarDatos();
    } catch (err) {
      setToast({ type: 'error', message: err instanceof Error ? err.message : 'Error al activar el prospecto' });
    }
  }

  function handleGtinActualizado(gtinActualizado: GtinRegistro) {
    setProducto((prev) =>
      prev
        ? {
            ...prev,
            gtin_registros: prev.gtin_registros.map((g) =>
              g.id === gtinActualizado.id ? gtinActualizado : g,
            ),
          }
        : prev,
    );
    setToast({ type: 'success', message: 'GTIN actualizado' });
  }

  async function handleDescargar(prospectoId: string) {
    try {
      const { url } = await obtenerUrlDescargaProspecto(prospectoId);
      window.open(url, '_blank');
    } catch (err) {
      setToast({ type: 'error', message: err instanceof Error ? err.message : 'Error al generar la descarga' });
    }
  }

  if (loading && !producto) {
    return <div className="min-h-screen bg-vent3-bg px-8 py-8 text-vent3-text-secondary">Cargando…</div>;
  }

  if (!producto) {
    return <div className="min-h-screen bg-vent3-bg px-8 py-8 text-vent3-text-secondary">Producto no encontrado</div>;
  }

  return (
    <div className="min-h-screen bg-vent3-bg px-8 py-8">
      {toast && (
        <div className="fixed right-8 top-8 z-10">
          <Toast type={toast.type} message={toast.message} />
        </div>
      )}

      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold text-vent3-text-primary">{producto.nombre_comercial}</h1>
          <p className="text-sm text-vent3-text-secondary">
            {producto.codigo_interno ?? '—'} · {producto.forma_farmaceutica} · {producto.presentacion_cantidad} ·{' '}
            {producto.canal}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={producto.estado === 'activo' ? 'success' : 'neutral'} label={producto.estado === 'activo' ? 'Activo' : 'Inactivo'} />
          <Button variant="secondary" size="sm" onClick={handleCambiarEstado}>
            {producto.estado === 'activo' ? 'Desactivar' : 'Activar'} producto
          </Button>
        </div>
      </div>

      <div className="mb-8">
        <h2 className="mb-2 text-sm font-medium text-vent3-text-primary">Principios activos</h2>
        <ul className="text-sm text-vent3-text-secondary">
          {producto.principios.map((p) => (
            <li key={p.id}>
              {p.nombre} {p.potencia} {p.unidad}
            </li>
          ))}
        </ul>
      </div>

      <div className="mb-8">
        <h2 className="mb-2 text-sm font-medium text-vent3-text-primary">GTINs</h2>
        <GtinTable gtinRegistros={producto.gtin_registros} onActualizado={handleGtinActualizado} />
      </div>

      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-medium text-vent3-text-primary">Prospectos</h2>
        {!mostrarUpload && (
          <Button variant="primary" size="sm" onClick={() => setMostrarUpload(true)}>
            Subir nuevo PDF
          </Button>
        )}
      </div>

      {mostrarUpload && (
        <div className="mb-6">
          <UploadProspecto
            productoId={productoId}
            onSubido={handleSubido}
            onCancelar={() => setMostrarUpload(false)}
          />
        </div>
      )}

      <div className="flex flex-col gap-2">
        {prospectos.length === 0 && (
          <p className="text-sm text-vent3-text-secondary">Todavía no hay prospectos para este producto.</p>
        )}
        {prospectos.map((prospecto) => {
          const badge = ESTADO_VIGENCIA_BADGE[prospecto.estado_vigencia] ?? {
            variant: 'neutral' as const,
            label: prospecto.estado_vigencia,
          };
          return (
            <div
              key={prospecto.id}
              className="flex items-center justify-between rounded-md border border-vent3-border bg-vent3-surface px-4 py-3"
            >
              <div>
                <p className="text-sm font-medium text-vent3-text-primary">
                  {prospecto.numero_expediente} · v{prospecto.version} · {prospecto.tipo_audiencia}
                </p>
                <p className="text-xs text-vent3-text-secondary">{prospecto.nombre_archivo}</p>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant={badge.variant} label={badge.label} />
                <Button variant="ghost" size="sm" onClick={() => handleDescargar(prospecto.id)}>
                  Descargar
                </Button>
                {prospecto.estado_vigencia === 'en_revision' && (
                  <Button variant="secondary" size="sm" onClick={() => handleActivar(prospecto.id)}>
                    Activar
                  </Button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
