import Link from 'next/link';
import NavMobile from '../../components/institucional/NavMobile';

const links = [
  { href: '/', label: 'Home' },
  { href: '/nosotros', label: 'Nosotros' },
  { href: '/productos', label: 'Productos' },
  { href: '/contacto', label: 'Contacto' },
];

export default function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      <a
        href="#contenido-principal"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-vent3-primary focus:px-4 focus:py-2 focus:text-vent3-bg"
      >
        Saltar al contenido principal
      </a>
      <header className="relative border-b border-vent3-border bg-vent3-bg">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-8">
          <Link href="/" className="font-sans text-xl font-bold text-vent3-primary">
            Vent3
          </Link>
          <nav className="hidden gap-6 sm:flex">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-vent3-text-primary hover:text-vent3-primary"
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <NavMobile />
        </div>
      </header>

      <main id="contenido-principal" className="flex-1">{children}</main>

      <footer className="border-t border-vent3-border bg-vent3-surface">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-8 text-sm text-vent3-text-secondary sm:px-8">
          <p className="font-sans font-semibold text-vent3-text-primary">Laboratorio Vent3</p>
          <p>
            {/* Datos de contacto placeholder — reemplazar por los reales antes de producción */}
            Córdoba, Argentina · contacto@vent3.com.ar · +54 351 000-0000
          </p>
          <p>
            Prospectos digitales conforme a ANMAT Disposición N° 2891/2026 y estándar GS1 Digital
            Link.
          </p>
          <p>© {new Date().getFullYear()} Laboratorio Vent3. Todos los derechos reservados.</p>
        </div>
      </footer>
    </div>
  );
}
