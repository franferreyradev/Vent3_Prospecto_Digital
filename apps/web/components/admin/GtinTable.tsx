'use client';

import type { components } from '@vent3/contracts';
import { useState } from 'react';
import { actualizarGtin } from '../../lib/api-client';
import Badge from '../ui/Badge';
import Button from '../ui/Button';
import Input from '../ui/Input';

type GtinRegistro = components['schemas']['GtinRegistroResponse'];

interface GtinTableProps {
  gtinRegistros: GtinRegistro[];
  onActualizado: (gtin: GtinRegistro) => void;
  rolUsuario: string;
}

export default function GtinTable({ gtinRegistros, onActualizado, rolUsuario }: GtinTableProps) {
  const esAdmin = rolUsuario === 'admin';
  const [editandoId, setEditandoId] = useState<string | null>(null);
  const [numeroGtin, setNumeroGtin] = useState('');
  const [gtinBloqueado, setGtinBloqueado] = useState(false);
  const [esVigente, setEsVigente] = useState(false);
  const [urlDigitalLink, setUrlDigitalLink] = useState('');
  const [qrGenerado, setQrGenerado] = useState(false);
  const [validadoGs1, setValidadoGs1] = useState(false);
  const [error, setError] = useState('');
  const [guardando, setGuardando] = useState(false);
  const [confirmacion, setConfirmacion] = useState<{
    id: string;
    tipo: 'bloqueo' | 'desbloqueo';
    gtinTexto: string;
  } | null>(null);

  function handleEditar(gtin: GtinRegistro) {
    setEditandoId(gtin.id);
    setNumeroGtin(gtin.gtin);
    setGtinBloqueado(gtin.qr_generado);
    setEsVigente(gtin.es_vigente);
    setUrlDigitalLink(gtin.url_digital_link ?? '');
    setQrGenerado(gtin.qr_generado);
    setValidadoGs1(gtin.validado_gs1);
    setError('');
  }

  function handleCancelar() {
    setEditandoId(null);
    setError('');
  }

  function handleGuardar(gtin: GtinRegistro) {
    setError('');

    const gtinModificado = !gtinBloqueado && numeroGtin !== gtin.gtin;
    const bloqueando = gtinModificado && qrGenerado;
    const desbloqueando = esAdmin && gtin.qr_generado && !qrGenerado;

    if (bloqueando) {
      setConfirmacion({ id: gtin.id, tipo: 'bloqueo', gtinTexto: numeroGtin });
      return;
    }
    if (desbloqueando) {
      setConfirmacion({ id: gtin.id, tipo: 'desbloqueo', gtinTexto: gtin.gtin });
      return;
    }
    void ejecutarGuardado(gtin.id);
  }

  async function ejecutarGuardado(id: string) {
    setGuardando(true);
    try {
      const actualizado = await actualizarGtin(id, {
        ...(gtinBloqueado ? {} : { gtin: numeroGtin }),
        es_vigente: esVigente,
        url_digital_link: urlDigitalLink || null,
        qr_generado: qrGenerado,
        validado_gs1: validadoGs1,
      });
      onActualizado(actualizado);
      setEditandoId(null);
      setConfirmacion(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al guardar el GTIN');
      setConfirmacion(null);
    } finally {
      setGuardando(false);
    }
  }

  if (gtinRegistros.length === 0) {
    return <p className="text-sm text-vent3-text-secondary">Este producto no tiene GTINs registrados.</p>;
  }

  return (
    <>
      {confirmacion && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-lg bg-vent3-bg p-6 shadow-xl">
            <h2 className="text-lg font-semibold text-vent3-text-primary">
              {confirmacion.tipo === 'bloqueo'
                ? 'Acción irreversible: se va a marcar el QR como generado'
                : 'Se va a desmarcar el QR generado'}
            </h2>
            <p className="mt-2 text-sm text-vent3-text-secondary">
              {confirmacion.tipo === 'bloqueo'
                ? 'A partir de este guardado, el GTIN queda inmutable: no vas a poder modificarlo salvo que un administrador desmarque nuevamente esta casilla. Verificá que el GTIN sea el correcto antes de continuar.'
                : 'Esto reabre la edición del GTIN de un registro que ya tenía el QR marcado como generado. Usalo solo para corregir un error de carga: si el QR ya está impreso en el packaging físico, cambiar el GTIN después rompe el código en circulación.'}
            </p>
            <div className="mt-4 rounded-md border border-vent3-border bg-vent3-surface px-3 py-2 font-mono text-sm text-vent3-text-primary">
              GTIN: {confirmacion.gtinTexto}
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={() => setConfirmacion(null)}>
                Cancelar
              </Button>
              <Button
                variant="primary"
                size="sm"
                loading={guardando}
                onClick={() => void ejecutarGuardado(confirmacion.id)}
              >
                Confirmar y guardar
              </Button>
            </div>
          </div>
        </div>
      )}
      <table className="w-full border-collapse text-left">
        <thead>
          <tr className="border-b border-vent3-border">
            <th className="px-4 py-2 text-sm font-medium text-vent3-text-secondary">GTIN</th>
            <th className="px-4 py-2 text-sm font-medium text-vent3-text-secondary">Vigente</th>
            <th className="px-4 py-2 text-sm font-medium text-vent3-text-secondary">Digital Link</th>
            <th className="px-4 py-2 text-sm font-medium text-vent3-text-secondary">QR generado</th>
            <th className="px-4 py-2 text-sm font-medium text-vent3-text-secondary">Validado GS1</th>
            <th className="px-4 py-2 text-sm font-medium text-vent3-text-secondary" />
          </tr>
        </thead>
        <tbody>
          {gtinRegistros.map((gtin) => {
            const enEdicion = editandoId === gtin.id;
            const bloqueadoParaNoAdmin = gtin.qr_generado && !esAdmin;

            return (
              <tr key={gtin.id} className="border-b border-vent3-border align-top">
                <td className="px-4 py-3 font-mono text-sm text-vent3-text-primary">
                  {enEdicion && !gtinBloqueado ? (
                    <Input
                      label="GTIN"
                      type="text"
                      value={numeroGtin}
                      onChange={(e) => setNumeroGtin(e.target.value)}
                      placeholder="14 dígitos"
                    />
                  ) : (
                    <>
                      {gtin.gtin}
                      {enEdicion && gtinBloqueado && (
                        <p className="mt-1 font-sans text-xs font-normal text-vent3-text-secondary">
                          No se puede modificar: ya tiene QR generado.
                        </p>
                      )}
                    </>
                  )}
                </td>
                <td className="px-4 py-3">
                  {enEdicion ? (
                    <div className="flex flex-col gap-1">
                      <label className="flex items-center gap-2 text-sm text-vent3-text-primary">
                        <input
                          type="checkbox"
                          checked={esVigente}
                          onChange={(e) => setEsVigente(e.target.checked)}
                        />
                        Vigente
                      </label>
                      {esVigente && !gtin.es_vigente && (
                        <p className="font-sans text-xs font-normal text-vent3-text-secondary">
                          Reemplaza al GTIN vigente actual de este producto, si hay uno.
                        </p>
                      )}
                    </div>
                  ) : (
                    <Badge
                      variant={gtin.es_vigente ? 'success' : 'neutral'}
                      label={gtin.es_vigente ? 'Sí' : 'No'}
                    />
                  )}
                </td>

                {enEdicion ? (
                  <>
                    <td className="px-4 py-3">
                      <Input
                        label="URL Digital Link"
                        type="text"
                        value={urlDigitalLink}
                        onChange={(e) => setUrlDigitalLink(e.target.value)}
                        placeholder="https://www.vent3.com.ar/01/..."
                        disabled={bloqueadoParaNoAdmin}
                        helperText={
                          bloqueadoParaNoAdmin
                            ? 'No se puede modificar: solo un administrador puede revertir un QR ya generado.'
                            : undefined
                        }
                      />
                    </td>
                    <td className="px-4 py-3">
                      <label className="flex items-center gap-2 text-sm text-vent3-text-primary">
                        <input
                          type="checkbox"
                          checked={qrGenerado}
                          disabled={bloqueadoParaNoAdmin}
                          onChange={(e) => setQrGenerado(e.target.checked)}
                        />
                        Generado
                      </label>
                      {bloqueadoParaNoAdmin && (
                        <p className="mt-1 text-xs font-normal text-vent3-text-secondary">
                          Solo un administrador puede desmarcarla.
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <label className="flex items-center gap-2 text-sm text-vent3-text-primary">
                        <input
                          type="checkbox"
                          checked={validadoGs1}
                          onChange={(e) => setValidadoGs1(e.target.checked)}
                        />
                        Validado
                      </label>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-col gap-2">
                        {error && <p className="text-sm text-vent3-danger">{error}</p>}
                        <div className="flex gap-2">
                          <Button
                            variant="primary"
                            size="sm"
                            loading={guardando}
                            onClick={() => handleGuardar(gtin)}
                          >
                            Guardar
                          </Button>
                          <Button variant="ghost" size="sm" onClick={handleCancelar}>
                            Cancelar
                          </Button>
                        </div>
                      </div>
                    </td>
                  </>
                ) : (
                  <>
                    <td className="px-4 py-3 text-sm text-vent3-text-secondary">
                      {gtin.url_digital_link ?? '—'}
                    </td>
                    <td className="px-4 py-3">
                      <Badge
                        variant={gtin.qr_generado ? 'success' : 'neutral'}
                        label={gtin.qr_generado ? 'Sí' : 'No'}
                      />
                    </td>
                    <td className="px-4 py-3">
                      <Badge
                        variant={gtin.validado_gs1 ? 'success' : 'neutral'}
                        label={gtin.validado_gs1 ? 'Sí' : 'No'}
                      />
                    </td>
                    <td className="px-4 py-3">
                      <Button variant="secondary" size="sm" onClick={() => handleEditar(gtin)}>
                        Editar
                      </Button>
                    </td>
                  </>
                )}
              </tr>
            );
          })}
        </tbody>
      </table>
    </>
  );
}
