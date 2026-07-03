import Badge from '../../../components/ui/Badge';
import PDFViewer from '../../../components/ui/PDFViewer';
import InteractiveDemo from '../../../components/dev/InteractiveDemo';

export default function DevComponentsPage() {
  return (
    <main className="mx-auto flex max-w-4xl flex-col gap-10 p-8">
      <h1 className="text-2xl font-bold">/dev/components — verificación visual T16</h1>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">Badge</h2>
        <div className="flex flex-wrap gap-3">
          <Badge variant="success" label="Activo" />
          <Badge variant="warning" label="Pendiente" />
          <Badge variant="danger" label="Vencido" />
          <Badge variant="neutral" label="Sin datos" />
        </div>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-semibold">PDFViewer</h2>
        <PDFViewer
          url="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
          fileName="prospecto-ejemplo.pdf"
        />
        <p className="text-sm text-vent3-text-secondary">
          Nota: el iframe puede quedar en blanco si la URL de prueba no resuelve en este
          entorno — no es un bug del componente, es una URL placeholder pública.
        </p>
      </section>

      <InteractiveDemo />
    </main>
  );
}
