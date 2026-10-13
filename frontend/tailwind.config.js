/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        obsidian: {
          DEFAULT: '#000000',
          950: '#020202',
          900: '#050505',
          850: '#09090b',
          800: '#0f0f12',
          750: '#141418',
          700: '#18181b',
          600: '#27272a',
          500: '#3f3f46',
        },
        silver: {
          DEFAULT: '#d4d4d8',
          50: '#fafafa',
          100: '#f4f4f5',
          200: '#e4e4e7',
          300: '#d4d4d8',
          400: '#a1a1aa',
          500: '#71717a',
          600: '#52525b',
          700: '#3f3f46',
          800: '#27272a',
          900: '#18181b',
        },
        navy: {
          950: '#000000',
          900: '#050505',
          850: '#09090b',
          800: '#121214',
          700: '#18181b',
          600: '#27272a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'Consolas', 'monospace'],
      },
      letterSpacing: {
        'ultra-wide': '0.25em',
        'mega-wide': '0.35em',
      },
    },
  },
  plugins: [],
}

