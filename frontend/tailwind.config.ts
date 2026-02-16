import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0D0D0D",
        card: "#1A1A1A",
        "card-hover": "#252525",
        border: "#333333",
        "muted-foreground": "#A0A0A0",
        signal: {
          green: "#22C55E",
          yellow: "#EAB308",
          red: "#EF4444",
          blue: "#3B82F6",
        },
        accent: {
          purple: "#8B5CF6",
        },
      },
    },
  },
  plugins: [],
};

export default config;
