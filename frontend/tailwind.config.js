/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        institucional: {
          950: "#0d1b2e",
          900: "#122544",
          800: "#1a3560",
          700: "#254a82",
          100: "#e7ecf5",
          50: "#f5f7fb",
        },
        acento: {
          600: "#b5762a",
          500: "#c98a3d",
          100: "#f4e6d3",
        },
      },
      fontFamily: {
        display: ["'Source Serif 4'", "Georgia", "serif"],
        sans: ["'Inter'", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
