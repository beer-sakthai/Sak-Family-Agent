/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        thai: {
          gold: "#d9b54a",
          bronze: "#c9813f",
          dark: "#0a0a0c",
          glass: "rgba(20, 20, 25, 0.7)",
        }
      },
      backgroundImage: {
        'premium-gradient': 'radial-gradient(circle at 50% 0%, #1a1a24 0%, #0a0a0c 60%)',
      }
    },
  },
  plugins: [],
}
