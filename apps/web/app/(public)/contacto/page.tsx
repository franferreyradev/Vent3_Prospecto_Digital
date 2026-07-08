import type { Metadata } from 'next';
import ContactoForm from '../../../components/institucional/ContactoForm';

export const metadata: Metadata = {
  title: 'Contacto — Laboratorio Vent3',
  description:
    'Contactate con Laboratorio Vent3, Córdoba, Argentina. Consultas comerciales, institucionales o sobre nuestros productos.',
  openGraph: {
    title: 'Contacto — Laboratorio Vent3',
    description: 'Contactate con Laboratorio Vent3, Córdoba, Argentina.',
    type: 'website',
    url: 'https://www.vent3.com.ar/contacto',
  },
};

export default function ContactoPage() {
  return (
    <section className="mx-auto max-w-6xl px-4 py-16 sm:px-8">
      <h1 className="font-serif text-3xl font-bold text-vent3-text-primary sm:text-4xl">
        Contacto
      </h1>
      <p className="mt-4 max-w-xl text-vent3-text-secondary">
        Completá el formulario y se abrirá tu cliente de correo con la consulta lista para enviar.
      </p>

      <div className="mt-10">
        <ContactoForm />
      </div>
    </section>
  );
}
