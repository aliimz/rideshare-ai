/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          green: '#22c55e',
          'green-dark': '#16a34a',
          'green-light': '#4ade80',
        },
        surface: {
          950: '#0f172a',
          900: '#1e293b',
          800: '#334155',
          700: '#475569',
        },
      },
      animation: {
        'pulse-slow': 'pulse 2.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fill-bar': 'fillBar 1.2s ease-out forwards',
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.35s ease-out',
        'ping-slow': 'ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite',
      },
      keyframes: {
        fillBar: {
          from: { width: '0%' },
          to: { width: 'var(--bar-width)' },
        },
        fadeIn: {
          from: { opacity: 0 },
          to: { opacity: 1 },
        },
        slideUp: {
          from: { opacity: 0, transform: 'translateY(12px)' },
          to: { opacity: 1, transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};
