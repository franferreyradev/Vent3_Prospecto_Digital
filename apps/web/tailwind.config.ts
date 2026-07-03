import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'vent3-primary': '#0B5394',      // Azul corporativo (a confirmar con identidad de marca)
        'vent3-secondary': '#3D85C6',
        'vent3-accent': '#E69138',
        'vent3-bg': '#FFFFFF',
        'vent3-surface': '#F5F7FA',
        'vent3-text-primary': '#1A1A1A',
        'vent3-text-secondary': '#5F6368',
        'vent3-border': '#D0D7DE',
        'vent3-success': '#1A8754',
        'vent3-warning': '#F0A020',
        'vent3-danger': '#C72424',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        serif: ['Source Serif Pro', 'Georgia', 'serif'],
      },
      maxWidth: {
        'prospecto': '900px',  // Ancho óptimo para lectura del PDF en desktop
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
  ],
};

export default config;
