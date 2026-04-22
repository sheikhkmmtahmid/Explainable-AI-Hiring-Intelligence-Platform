/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        scarlet: {
          50:  '#fff0f0',
          100: '#ffd6d6',
          200: '#ffb0b0',
          300: '#ff7a7a',
          400: '#ff3d3d',
          500: '#AE0001',
          600: '#8b0001',
          700: '#740001',
          800: '#5a0001',
          900: '#3d0001',
        },
        gold: {
          400: '#e8bc2e',
          500: '#D3A625',
          600: '#b08a1a',
        },
        surface: {
          50:  '#f5f5f5',
          900: '#0A0A0A',
          800: '#111111',
          700: '#181818',
          600: '#1E1E1E',
          500: '#252525',
          400: '#2E2E2E',
          300: '#3A3A3A',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'scarlet': '0 0 20px rgba(174, 0, 1, 0.3)',
        'scarlet-sm': '0 0 8px rgba(174, 0, 1, 0.2)',
        'card': '0 1px 3px rgba(0,0,0,0.5)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp: { from: { opacity: 0, transform: 'translateY(12px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [],
}
