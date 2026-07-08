import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Laboratorio Vent3 — Prospectos digitales certificados ANMAT',
  description:
    'Laboratorio Vent3, Córdoba. Accedé al prospecto digital de nuestros productos mediante el código QR del packaging, conforme a ANMAT Disposición N° 2891/2026.',
  openGraph: {
    title: 'Laboratorio Vent3',
    description:
      'Prospectos digitales certificados ANMAT, accesibles mediante el código QR del packaging de cada producto.',
    type: 'website',
    url: 'https://www.vent3.com.ar/',
  },
};

export default function HomePage() {
  return (
    <>
      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-8">
        <h1 className="max-w-2xl font-serif text-4xl font-bold leading-tight text-vent3-text-primary sm:text-5xl">
          Salud y confianza, en cada envase.
        </h1>
        <p className="mt-6 max-w-xl text-lg text-vent3-text-secondary">
          Laboratorio Vent3 desarrolla medicamentos con los más altos estándares de calidad,
          acompañados de prospectos digitales certificados ANMAT, accesibles al instante desde el
          QR de cada producto.
        </p>
        <div className="mt-8 flex gap-4">
          <Link
            href="/productos"
            className="rounded-md bg-vent3-primary px-6 py-3 font-medium text-vent3-bg hover:bg-vent3-secondary"
          >
            Conocer nuestros productos
          </Link>
          <Link
            href="/contacto"
            className="rounded-md border border-vent3-border px-6 py-3 font-medium text-vent3-text-primary hover:bg-vent3-surface"
          >
            Contactanos
          </Link>
        </div>
      </section>

      <section className="border-t border-vent3-border bg-vent3-surface">
        <div className="mx-auto max-w-6xl px-4 py-16 sm:px-8">
          <h2 className="font-sans text-2xl font-bold text-vent3-text-primary">
            Líneas de productos
          </h2>
          <p className="mt-2 max-w-2xl text-vent3-text-secondary">
            Desarrollamos medicamentos en distintas líneas terapéuticas, cada uno con su
            prospecto digital vigente disponible mediante el QR del packaging.
          </p>
          <Link
            href="/productos"
            className="mt-6 inline-block font-medium text-vent3-primary hover:underline"
          >
            Ver líneas de productos →
          </Link>
        </div>
      </section>
    </>
  );
}
