import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Productos — Laboratorio Vent3',
  description:
    'Líneas terapéuticas del Laboratorio Vent3. Información general, no el detalle de prospectos por producto.',
  openGraph: {
    title: 'Productos — Laboratorio Vent3',
    description: 'Líneas terapéuticas del Laboratorio Vent3.',
    type: 'website',
    url: 'https://www.vent3.com.ar/productos',
  },
};

// Contenido estático e informativo — no consume GET /api/productos (requiere auth de admin).
const lineas = [
  {
    nombre: 'Analgésicos y antiinflamatorios',
    descripcion: 'Medicamentos para el manejo del dolor y procesos inflamatorios.',
  },
  {
    nombre: 'Antibióticos',
    descripcion: 'Tratamientos antimicrobianos para infecciones bacterianas.',
  },
  {
    nombre: 'Cardiovascular',
    descripcion: 'Medicamentos para el manejo de la presión arterial y la salud cardiovascular.',
  },
  {
    nombre: 'Sistema respiratorio',
    descripcion: 'Tratamientos para afecciones respiratorias agudas y crónicas.',
  },
];

export default function ProductosPage() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-16 sm:px-8">
      <h1 className="font-serif text-3xl font-bold text-vent3-text-primary sm:text-4xl">
        Líneas de productos
      </h1>
      <p className="mt-4 max-w-2xl text-vent3-text-secondary">
        Desarrollamos medicamentos en las siguientes líneas terapéuticas. El prospecto vigente de
        cada producto está disponible escaneando el código QR de su packaging.
      </p>

      <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2">
        {lineas.map((linea) => (
          <div
            key={linea.nombre}
            className="rounded-lg border border-vent3-border bg-vent3-surface p-6"
          >
            <h2 className="font-sans text-lg font-bold text-vent3-text-primary">
              {linea.nombre}
            </h2>
            <p className="mt-2 text-vent3-text-secondary">{linea.descripcion}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
