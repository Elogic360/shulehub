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
          navy: '#0A2540',
          darkNavy: '#051329',
          lightNavy: '#1E3A8A',
          teal: '#00D4B2',
          darkTeal: '#00A389',
          accent: '#38BDF8',
          bgSurface: '#F8FAFC',
          borderSubtle: '#E2E8F0',
        }
      }
    },
  },
  plugins: [],
}
