/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        institutional: {
          DEFAULT: "#1E3A8A",
          dark: "#152a63",
        },
      },
    },
  },
  plugins: [],
};
