import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f9ff', 100: '#e0f2fe', 200: '#bae6fd',
          500: '#0ea5e9', 600: '#0284c7', 700: '#0369a1',
        },
        surface: {
          DEFAULT: '#0d1117',
          card: '#111827',
          hover: '#1a2332',
          border: '#1f2937',
          muted: '#374151',
        },
      },
      fontFamily: { sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'] },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.25s ease-out',
      },
      keyframes: {
        fadeIn: { '0%': { opacity: '0' }, '100%': { opacity: '1' } },
        slideUp: { '0%': { opacity: '0', transform: 'translateY(8px)' }, '100%': { opacity: '1', transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [],
} satisfies Config
