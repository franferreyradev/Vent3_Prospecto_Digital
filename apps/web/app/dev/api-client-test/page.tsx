'use client';

import { useState } from 'react';
import { getMe, login, ApiError } from '../../../lib/api-client';

export default function ApiClientTestPage() {
  const [log, setLog] = useState<string[]>([]);

  function append(line: string) {
    setLog((prev) => [...prev, line]);
  }

  async function probarMe() {
    append('Llamando a GET /api/auth/me sin sesión...');
    try {
      const usuario = await getMe();
      append(`OK inesperado: ${JSON.stringify(usuario)}`);
    } catch (error) {
      if (error instanceof ApiError) {
        append(`ApiError capturado: status=${error.status} detail="${error.message}"`);
      } else {
        append(`Error no tipado: ${String(error)}`);
      }
    }
  }

  async function probarLoginInvalido() {
    append('Llamando a POST /api/auth/login con credenciales inválidas...');
    try {
      await login({ email: 'noexiste@vent3.com.ar', password: 'incorrecta' });
      append('OK inesperado: login no debería haber tenido éxito');
    } catch (error) {
      if (error instanceof ApiError) {
        append(`ApiError capturado (sin redirect): status=${error.status} detail="${error.message}"`);
      } else {
        append(`Error no tipado: ${String(error)}`);
      }
    }
  }

  return (
    <main style={{ padding: 24, fontFamily: 'monospace' }}>
      <h1>T17 — Prueba manual de api-client.ts</h1>
      <button onClick={probarMe}>Probar /api/auth/me (sin cookie)</button>
      <button onClick={probarLoginInvalido}>Probar login inválido (no debe redirigir)</button>
      <ul>
        {log.map((line, i) => (
          <li key={i}>{line}</li>
        ))}
      </ul>
    </main>
  );
}
