'use client';

import { useState } from 'react';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Select from '../ui/Select';
import Table, { ColumnDef } from '../ui/Table';
import SelectorAudiencia from '../ui/SelectorAudiencia';
import Toast from '../ui/Toast';

interface ProductoMock {
  id: string;
  nombre: string;
  estado: string;
}

const productosMock: ProductoMock[] = [
  { id: '1', nombre: 'Ibuprofeno 400mg', estado: 'Activo' },
  { id: '2', nombre: 'Amoxicilina 500mg', estado: 'Activo' },
  { id: '3', nombre: 'Loratadina 10mg', estado: 'Inactivo' },
];

const columnasMock: ColumnDef<ProductoMock>[] = [
  { key: 'nombre', header: 'Nombre' },
  { key: 'estado', header: 'Estado' },
];

export default function InteractiveDemo() {
  const [clicks, setClicks] = useState(0);
  const [inputValue, setInputValue] = useState('');
  const [selectValue, setSelectValue] = useState('opcion1');
  const [selectedProducto, setSelectedProducto] = useState<string | null>(null);
  const [audiencia, setAudiencia] = useState<string | null>(null);

  return (
    <div className="flex flex-col gap-10">
      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Button</h2>
        <div className="flex flex-wrap gap-3">
          <Button variant="primary" onClick={() => setClicks((c) => c + 1)}>
            Primary
          </Button>
          <Button variant="secondary" onClick={() => setClicks((c) => c + 1)}>
            Secondary
          </Button>
          <Button variant="ghost" onClick={() => setClicks((c) => c + 1)}>
            Ghost
          </Button>
          <Button variant="danger" onClick={() => setClicks((c) => c + 1)}>
            Danger
          </Button>
          <Button variant="primary" loading>
            Cargando
          </Button>
        </div>
        <p className="text-sm text-vent3-text-secondary">Clicks registrados: {clicks}</p>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Input</h2>
        <Input
          label="Nombre de producto"
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          helperText="Escribí algo para verificar el estado controlado"
        />
        <Input label="Email inválido" type="email" defaultValue="no-es-un-email" error="Ingresá un email válido" />
        <p className="text-sm text-vent3-text-secondary">Valor actual: {inputValue || '(vacío)'}</p>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Select</h2>
        <Select
          label="Canal"
          value={selectValue}
          onChange={setSelectValue}
          options={[
            { value: 'opcion1', label: 'Farmacia' },
            { value: 'opcion2', label: 'Hospitalario' },
            { value: 'opcion3', label: 'Licitación' },
          ]}
        />
        <p className="text-sm text-vent3-text-secondary">Seleccionado: {selectValue}</p>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Table</h2>
        <Table
          columns={columnasMock}
          data={productosMock}
          onRowClick={(row) => setSelectedProducto(row.nombre)}
        />
        <p className="text-sm text-vent3-text-secondary">
          Fila seleccionada: {selectedProducto ?? '(ninguna)'}
        </p>
        <h3 className="text-sm font-semibold">Estado loading</h3>
        <Table columns={columnasMock} data={[]} loading />
        <h3 className="text-sm font-semibold">Sin resultados</h3>
        <Table columns={columnasMock} data={[]} />
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">SelectorAudiencia</h2>
        <SelectorAudiencia onSelect={setAudiencia} />
        <p className="text-sm text-vent3-text-secondary">Audiencia elegida: {audiencia ?? '(ninguna)'}</p>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Toast (auto-dismiss a los 4s / 6s / 8s)</h2>
        <div className="flex flex-col gap-2">
          <Toast type="success" message="Prospecto subido correctamente" duration={4000} />
          <Toast type="error" message="No se pudo guardar el cambio" duration={6000} />
          <Toast type="info" message="El PDF se está procesando" duration={8000} />
        </div>
      </section>
    </div>
  );
}
