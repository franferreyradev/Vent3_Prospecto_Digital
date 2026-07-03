const tokens = [
  { nombre: 'vent3-primary', clase: 'bg-vent3-primary' },
  { nombre: 'vent3-secondary', clase: 'bg-vent3-secondary' },
  { nombre: 'vent3-accent', clase: 'bg-vent3-accent' },
  { nombre: 'vent3-bg', clase: 'bg-vent3-bg border border-vent3-border' },
  { nombre: 'vent3-surface', clase: 'bg-vent3-surface border border-vent3-border' },
  { nombre: 'vent3-text-primary', clase: 'bg-vent3-text-primary' },
  { nombre: 'vent3-text-secondary', clase: 'bg-vent3-text-secondary' },
  { nombre: 'vent3-border', clase: 'bg-vent3-border' },
  { nombre: 'vent3-success', clase: 'bg-vent3-success' },
  { nombre: 'vent3-warning', clase: 'bg-vent3-warning' },
  { nombre: 'vent3-danger', clase: 'bg-vent3-danger' },
];

export default function Home() {
  return (
    <main className="mx-auto max-w-prospecto p-8">
      <h1 className="mb-6 text-2xl font-sans font-bold text-vent3-text-primary">
        Vent3 — Design Tokens
      </h1>
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        {tokens.map((token) => (
          <div key={token.nombre} className="flex flex-col gap-2">
            <div className={`h-16 w-full rounded ${token.clase}`} />
            <span className="text-sm text-vent3-text-secondary">{token.nombre}</span>
          </div>
        ))}
      </div>
    </main>
  );
}
