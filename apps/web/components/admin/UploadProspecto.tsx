'use client';

import { useState } from 'react';
import { subirProspecto } from '../../lib/api-client';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Button from '../ui/Button';

type TipoAudiencia = 'publico_general' | 'profesional_salud' | 'unico';

interface UploadProspectoProps {
  productoId: string;
  onSubido: (prospectoId: string) => void;
  onCancelar: () => void;
}

export default function UploadProspecto({ productoId, onSubido, onCancelar }: UploadProspectoProps) {
  const [numeroExpediente, setNumeroExpediente] = useState('');
  const [version, setVersion] = useState('1');
  const [tipoAudiencia, setTipoAudiencia] = useState<TipoAudiencia>('unico');
  const [archivo, setArchivo] = useState<File | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');

    if (!archivo) {
      setError('Seleccioná un archivo PDF');
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('numero_expediente', numeroExpediente);
      formData.append('version', version);
      formData.append('tipo_audiencia', tipoAudiencia);
      formData.append('producto_id', productoId);
      formData.append('archivo', archivo);

      const prospecto = await subirProspecto(formData);
      onSubido(prospecto.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error al subir el prospecto');
    } finally {
      setLoading(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-4 rounded-md border border-vent3-border bg-vent3-surface p-4"
    >
      {error && <p className="text-sm text-vent3-danger">{error}</p>}

      <Input
        label="Número de expediente"
        type="text"
        value={numeroExpediente}
        onChange={(e) => setNumeroExpediente(e.target.value)}
        required
      />

      <Input
        label="Versión"
        type="text"
        inputMode="numeric"
        value={version}
        onChange={(e) => setVersion(e.target.value)}
        required
      />

      <Select
        label="Audiencia"
        value={tipoAudiencia}
        onChange={(v) => setTipoAudiencia(v as TipoAudiencia)}
        options={[
          { value: 'unico', label: 'Único' },
          { value: 'publico_general', label: 'Público general' },
          { value: 'profesional_salud', label: 'Profesional de salud' },
        ]}
      />

      <Input
        label="Archivo PDF"
        type="file"
        accept="application/pdf"
        onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
        required
      />

      <div className="flex gap-2">
        <Button type="submit" variant="primary" loading={loading}>
          Subir prospecto
        </Button>
        <Button type="button" variant="secondary" onClick={onCancelar} disabled={loading}>
          Cancelar
        </Button>
      </div>
    </form>
  );
}
