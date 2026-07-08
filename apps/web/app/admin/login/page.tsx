'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ApiError, login } from '../../../lib/api-client';
import Input from '../../../components/ui/Input';
import Button from '../../../components/ui/Button';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await login({ email, password });
      router.push('/admin');
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : 'Error inesperado al comunicarse con el servidor';
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-vent3-bg px-4">
      <form
        onSubmit={handleSubmit}
        className="flex w-full max-w-sm flex-col gap-4 rounded-lg border border-vent3-border bg-vent3-surface p-8"
      >
        <h1 className="text-xl font-semibold text-vent3-text-primary">Ingresar</h1>

        {error ? <p className="text-sm text-vent3-danger">{error}</p> : null}

        <Input
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />

        <Input
          label="Contraseña"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <Button type="submit" variant="primary" loading={loading}>
          Ingresar
        </Button>
      </form>
    </div>
  );
}
