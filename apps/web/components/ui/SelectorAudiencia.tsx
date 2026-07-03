'use client';

import Button from './Button';

type Audiencia = 'publico' | 'profesional';

interface SelectorAudienciaProps {
  onSelect: (audiencia: Audiencia) => void;
}

export default function SelectorAudiencia({ onSelect }: SelectorAudienciaProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row">
      <Button
        variant="primary"
        size="lg"
        className="flex-1"
        onClick={() => onSelect('publico')}
      >
        Soy paciente
      </Button>
      <Button
        variant="secondary"
        size="lg"
        className="flex-1"
        onClick={() => onSelect('profesional')}
      >
        Soy profesional de salud
      </Button>
    </div>
  );
}
