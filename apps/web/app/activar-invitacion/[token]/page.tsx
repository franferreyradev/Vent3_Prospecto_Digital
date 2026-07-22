'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { activarInvitacion, ApiError, validarInvitacion } from '../../../lib/api-client';
import Input from '../../../components/ui/Input';
import Button from '../../../components/ui/Button';

interface PageProps {
  params: { token: string };
}

type Estado =
  | { tipo: 'cargando' }
  | { tipo: 'invalida' }
  | { tipo: 'valida'; email: string; nombre: string; rol: string };

export default function ActivarInvitacionPage({ params }: PageProps) {
  const router = useRouter();
  const { token } = params;
  const [estado, setEstado] = useState<Estado>({ tipo: 'cargando' });
  const [password, setPassword] = useState('');
  const [confirmacion, setConfirmacion] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    validarInvitacion(token)
      .then((res) => setEstado({ tipo: 'valida', ...res }))
      .catch(() => setEstado({ tipo: 'invalida' }));
  }, [token]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (password !== confirmacion) {
      setError('Las contraseñas no coinciden');
      return;
    }

    setEnviando(true);
    try {
      await activarInvitacion(token, { password });
      router.push('/admin');
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : 'Error inesperado al comunicarse con el servidor';
      setError(message);
    } finally {
      setEnviando(false);
    }
  }

  if (estado.tipo === 'cargando') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-vent3-bg px-4">
        <p className="text-sm text-vent3-text-secondary">Verificando invitación...</p>
      </div>
    );
  }

  if (estado.tipo === 'invalida') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-vent3-bg px-4">
        <div className="w-full max-w-sm rounded-lg border border-vent3-border bg-vent3-surface p-8 text-center">
          <h1 className="text-lg font-semibold text-vent3-text-primary">
            Invitación inválida o expirada
          </h1>
          <p className="mt-2 text-sm text-vent3-text-secondary">
            Este link ya no es válido. Pedile al administrador que te envíe uno nuevo.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-vent3-bg px-4">
      <form
        onSubmit={handleSubmit}
        className="flex w-full max-w-sm flex-col gap-4 rounded-lg border border-vent3-border bg-vent3-surface p-8"
      >
        <div>
          <h1 className="text-xl font-semibold text-vent3-text-primary">Activar tu cuenta</h1>
          <p className="mt-1 text-sm text-vent3-text-secondary">
            {estado.email} · {estado.rol}
          </p>
        </div>

        {error ? <p className="text-sm text-vent3-danger">{error}</p> : null}

        <Input
          label="Contraseña"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          minLength={8}
          required
        />

        <Input
          label="Confirmar contraseña"
          type="password"
          value={confirmacion}
          onChange={(e) => setConfirmacion(e.target.value)}
          minLength={8}
          required
        />

        <Button type="submit" variant="primary" loading={enviando}>
          Activar cuenta
        </Button>
      </form>
    </div>
  );
}
