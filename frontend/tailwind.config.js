/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: '#102A43',
          darkNavy: '#0B1D30',
          lightNavy: '#1E3A8A',
          teal: '#0D9488',
          darkTeal: '#0F766E',
          accent: '#38BDF8',
          actionBlue: '#2563EB',
          bgSurface: '#F8FAFC',
          borderSubtle: '#E2E8F0',
          textPrimary: '#0F172A',
          textSecondary: '#64748B',
          success: '#16A34A',
          warning: '#F59E0B',
          error: '#DC2626',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
