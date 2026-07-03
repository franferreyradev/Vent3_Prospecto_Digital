import type { Metadata } from 'next';
import type { components } from '@vent3/contracts';
import PDFViewer from '../../../components/ui/PDFViewer';
import LandingSelector from '../../../components/prospecto/LandingSelector';
import ErrorPage from '../../../components/prospecto/ErrorPage';

type ResolverResponse = components['schemas']['ResolverResponse'];

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const GTIN_REGEX = /^\d{14}$/;

interface PageProps {
  params: { gtin: string };
}

async function resolverGtin(gtin: string): Promise<ResolverResponse> {
  const response = await fetch(`${API_URL}/api/internal/prospectos/by-gtin/${gtin}`, {
    headers: { 'X-Internal-Token': process.env.INTERNAL_API_TOKEN ?? '' },
    cache: 'no-store',
  });

  if (!response.ok) {
    // 403 (token mal configurado) o 422 (no debería llegar acá, ya
    // validamos el formato antes) — error de infra, no de usuario final.
    return { producto: null, prospectos: [], error: 'no_encontrado', tiene_dos_prospectos: false, tipo_landing: 'error' };
  }

  return response.json() as Promise<ResolverResponse>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  if (!GTIN_REGEX.test(params.gtin)) {
    return { title: 'Prospecto no encontrado — Vent3' };
  }

  const data = await resolverGtin(params.gtin);
  return {
    title: data.producto ? `${data.producto.nombre_comercial} — Prospecto Vent3` : 'Prospecto no encontrado — Vent3',
  };
}

export default async function ProspectoPage({ params }: PageProps) {
  if (!GTIN_REGEX.test(params.gtin)) {
    return <ErrorPage error="no_encontrado" />;
  }

  const data = await resolverGtin(params.gtin);

  if (data.tipo_landing === 'error') {
    return <ErrorPage error={data.error ?? 'no_encontrado'} />;
  }

  if (data.tipo_landing === 'selector') {
    return (
      <main className="mx-auto flex min-h-screen max-w-prospecto flex-col gap-6 p-8">
        <h1 className="text-2xl font-bold text-vent3-text-primary">
          {data.producto?.nombre_comercial}
        </h1>
        <p className="text-vent3-text-secondary">Seleccioná tu perfil para ver el prospecto correspondiente.</p>
        <LandingSelector prospectos={data.prospectos} fileName={data.producto?.nombre_comercial} />
      </main>
    );
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-prospecto flex-col gap-6 p-8">
      <h1 className="text-2xl font-bold text-vent3-text-primary">
        {data.producto?.nombre_comercial}
      </h1>
      <PDFViewer url={data.prospectos[0].url_archivo} fileName={data.producto?.nombre_comercial} />
    </main>
  );
}
