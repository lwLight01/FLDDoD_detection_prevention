/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: "#0f172a",
        primary: "#3b82f6",
        accent: "#8b5cf6",
        danger: "#ef4444",
        warning: "#f59e0b",
        success: "#10b981",
      }
    },
  },
  plugins: [],
}
