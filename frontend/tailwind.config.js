/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Outfit', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        aurora: {
          indigo: '#4f46e5',
          violet: '#7c3aed',
          cyan: '#06b6d4',
          teal: '#14b8a6',
          bg: '#05050f',
          surface: '#0f0f1b',
          glass: 'rgba(15, 15, 27, 0.4)',
        }
      },
      animation: {
        'blob': 'blob 7s infinite',
        'pulse-slow': 'pulse-slow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        blob: {
          '0%': { transform: 'translate(0px, 0px) scale(1)' },
          '33%': { transform: 'translate(30px, -50px) scale(1.1)' },
          '66%': { transform: 'translate(-20px, 20px) scale(0.9)' },
          '100%': { transform: 'translate(0px, 0px) scale(1)' },
        },
        'pulse-slow': {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: .5 },
        },
        glow: {
          'from': { boxShadow: '0 0 10px -2px rgba(6, 182, 212, 0.2)' },
          'to': { boxShadow: '0 0 20px 2px rgba(6, 182, 212, 0.6)' },
        }
      }
    },
  },
  plugins: [],
}
