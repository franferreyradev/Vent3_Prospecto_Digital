import type { MetadataRoute } from 'next';

const BASE_URL = 'https://www.vent3.com.ar';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/admin/', '/dev/'],
    },
    sitemap: `${BASE_URL}/sitemap.xml`,
  };
}
