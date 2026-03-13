/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        binance: {
          yellow: '#F0B90B',
          dark: '#0B0E11',
          gray: '#1E2026',
          'gray-light': '#2B3139',
          'text-primary': '#EAECEF',
          'text-secondary': '#848E9C',
        },
      },
    },
  },
  plugins: [],
}
