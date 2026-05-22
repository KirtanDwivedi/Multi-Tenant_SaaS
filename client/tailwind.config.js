/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        chatgpt: {
          main: '#212121',
          sidebar: '#171717',
          hover: '#2f2f2f',
          input: '#303030',
        }
      }
    },
  },
  plugins: [],
}