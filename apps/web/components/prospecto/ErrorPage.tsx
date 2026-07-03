type TipoError = 'no_encontrado' | 'inactivo' | 'sin_prospecto';

interface ErrorPageProps {
  error: TipoError;
}

const MENSAJES: Record<TipoError, { titulo: string; descripcion: string }> = {
  no_encontrado: {
    titulo: 'Producto no encontrado',
    descripcion:
      'No pudimos encontrar información para el código escaneado. Verificá que el QR corresponda a un envase de Laboratorio Vent3 y volvé a intentarlo.',
  },
  inactivo: {
    titulo: 'Producto no disponible',
    descripcion:
      'Este producto no se encuentra disponible actualmente. Si tenés dudas sobre su uso, consultá con tu farmacéutico o profesional de salud.',
  },
  sin_prospecto: {
    titulo: 'Prospecto no disponible',
    descripcion:
      'Todavía no hay un prospecto cargado para este producto. Por favor, intentá nuevamente más tarde o consultá con tu farmacéutico.',
  },
};

export default function ErrorPage({ error }: ErrorPageProps) {
  const { titulo, descripcion } = MENSAJES[error];

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col items-center justify-center gap-4 p-8 text-center">
      <h1 className="text-2xl font-bold text-vent3-text-primary">{titulo}</h1>
      <p className="text-vent3-text-secondary">{descripcion}</p>
    </main>
  );
}
