/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        profit: "#059669",
        loss: "#DC2626",
      },
    },
  },
  plugins: [],
};
