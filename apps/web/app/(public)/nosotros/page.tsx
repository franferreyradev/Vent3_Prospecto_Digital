import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Nosotros — Laboratorio Vent3',
  description:
    'Conocé la historia y la misión del Laboratorio Vent3, Córdoba, Argentina. Compromiso con la calidad farmacéutica y el acceso a la información del paciente.',
  openGraph: {
    title: 'Nosotros — Laboratorio Vent3',
    description: 'Historia y misión del Laboratorio Vent3, Córdoba, Argentina.',
    type: 'website',
    url: 'https://www.vent3.com.ar/nosotros',
  },
};

export default function NosotrosPage() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-16 sm:px-8">
      <h1 className="font-serif text-3xl font-bold text-vent3-text-primary sm:text-4xl">
        Quiénes somos
      </h1>

      {/* Copy institucional placeholder — pendiente de contenido real antes de producción */}
      <div className="mt-8 flex flex-col gap-6 text-vent3-text-secondary">
        <p>
          Laboratorio Vent3 es una compañía farmacéutica argentina con sede en Córdoba, dedicada
          al desarrollo, producción y distribución de medicamentos de calidad, con foco en la
          seguridad del paciente y el acceso claro a la información terapéutica.
        </p>
        <p>
          Nuestra misión es acompañar a profesionales de la salud y pacientes con productos
          confiables, respaldados por procesos de calidad certificados y prospectos digitales
          siempre actualizados, en línea con las exigencias de ANMAT y el estándar internacional
          GS1 Digital Link.
        </p>
        <p>
          Trabajamos día a día para que cada envase que sale de nuestra planta lleve, además del
          medicamento, la información necesaria para su uso seguro y responsable.
        </p>
      </div>
    </section>
  );
}
