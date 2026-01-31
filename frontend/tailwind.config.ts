import type { Config } from "tailwindcss";

export default {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: "#a80000",
        "accent-gold": "#b3995d",
        "background-light": "#f8f5f5",
        "background-dark": "#181010",
        "panel-dark": "#230f0f",
        "border-subtle": "#3a2727",
        "text-muted": "#bc9a9a",
      },
      fontFamily: {
        display: ["Inter", "sans-serif"],
        mono: ["ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
