const SITIO_ANTERIOR_URL = 'https://actual.vent3.com.ar';

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Temporal: la web nueva todavía no tiene contenido/branding definitivo.
  // Todo el sitio redirige al WordPress anterior excepto /01/[gtin] (portal
  // de prospectos, ya en uso por QRs impresos en packaging en circulación).
  // Remover cuando la web nueva esté lista para producción.
  async redirects() {
    return [
      {
        source: '/:path((?!01(?:/|$)).*)',
        destination: SITIO_ANTERIOR_URL,
        permanent: false,
      },
    ];
  },
};

module.exports = nextConfig;
