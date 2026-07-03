'use client';

import { useState } from 'react';
import PDFViewer from '../ui/PDFViewer';
import SelectorAudiencia from '../ui/SelectorAudiencia';

type TipoAudienciaDominio = 'publico_general' | 'profesional_salud' | 'unico';
type TipoAudienciaUI = 'publico' | 'profesional';

interface ProspectoPublico {
  tipo_audiencia: string;
  url_archivo: string;
}

interface LandingSelectorProps {
  prospectos: ProspectoPublico[];
  fileName?: string;
}

const MAPA_AUDIENCIA: Record<TipoAudienciaUI, TipoAudienciaDominio> = {
  publico: 'publico_general',
  profesional: 'profesional_salud',
};

export default function LandingSelector({ prospectos, fileName }: LandingSelectorProps) {
  const [audiencia, setAudiencia] = useState<TipoAudienciaUI | null>(null);

  if (!audiencia) {
    return <SelectorAudiencia onSelect={setAudiencia} />;
  }

  const prospecto = prospectos.find(
    (p) => p.tipo_audiencia === MAPA_AUDIENCIA[audiencia],
  );

  if (!prospecto) {
    return <SelectorAudiencia onSelect={setAudiencia} />;
  }

  return <PDFViewer url={prospecto.url_archivo} fileName={fileName} />;
}
