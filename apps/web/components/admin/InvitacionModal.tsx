'use client';

import { FormEvent, useState } from 'react';
import { ApiError, crearInvitacion } from '../../lib/api-client';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';

interface InvitacionModalProps {
  onClose: () => void;
}

export default function InvitacionModal({ onClose }: InvitacionModalProps) {
  const [email, setEmail] = useState('');
  const [nombre, setNombre] = useState('');
  const [rol, setRol] = useState('editor');
  const [error, setError] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [link, setLink] = useState<string | null>(null);
  const [copiado, setCopiado] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setEnviando(true);
    setError('');
    try {
      const invitacion = await crearInvitacion({ email, nombre, rol: rol as 'admin' | 'editor' });
      setLink(invitacion.link);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Error al crear la invitación');
    } finally {
      setEnviando(false);
    }
  }

  async function handleCopiar() {
    if (!link) return;
    await navigator.clipboard.writeText(link);
    setCopiado(true);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg bg-vent3-bg p-6 shadow-xl">
        {link ? (
          <>
            <h2 className="text-lg font-semibold text-vent3-text-primary">
              Invitación creada
            </h2>
            <p className="mt-2 text-sm text-vent3-text-secondary">
              Compartí este link con {email}. Es de un solo uso y expira en 48 horas — esta es la
              única vez que vas a poder verlo.
            </p>
            <div className="mt-4 flex gap-2">
              <input
                readOnly
                value={link}
                className="w-full rounded-md border border-vent3-border bg-vent3-surface px-3 py-2 font-mono text-sm text-vent3-text-primary"
                onFocus={(e) => e.target.select()}
              />
              <Button variant="secondary" size="sm" onClick={() => void handleCopiar()}>
                {copiado ? 'Copiado' : 'Copiar'}
              </Button>
            </div>
            <div className="mt-6 flex justify-end">
              <Button variant="primary" size="sm" onClick={onClose}>
                Listo
              </Button>
            </div>
          </>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <h2 className="text-lg font-semibold text-vent3-text-primary">Nueva invitación</h2>

            {error && <p className="text-sm text-vent3-danger">{error}</p>}

            <Input
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
            <Input
              label="Nombre"
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              required
            />
            <Select
              label="Rol"
              value={rol}
              onChange={setRol}
              options={[
                { value: 'editor', label: 'Editor' },
                { value: 'admin', label: 'Admin' },
              ]}
            />

            <div className="mt-2 flex justify-end gap-2">
              <Button type="button" variant="ghost" size="sm" onClick={onClose}>
                Cancelar
              </Button>
              <Button type="submit" variant="primary" size="sm" loading={enviando}>
                Crear invitación
              </Button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
