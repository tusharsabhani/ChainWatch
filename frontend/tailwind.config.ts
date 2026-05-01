import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        background: "rgb(var(--color-background) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        "surface-dim": "rgb(var(--color-surface-dim) / <alpha-value>)",
        "surface-container-lowest": "rgb(var(--color-surface-container-lowest) / <alpha-value>)",
        "surface-container-low": "rgb(var(--color-surface-container-low) / <alpha-value>)",
        "surface-container": "rgb(var(--color-surface-container) / <alpha-value>)",
        "surface-container-high": "rgb(var(--color-surface-container-high) / <alpha-value>)",
        "surface-container-highest": "rgb(var(--color-surface-container-highest) / <alpha-value>)",
        "surface-variant": "rgb(var(--color-surface-variant) / <alpha-value>)",
        "on-background": "rgb(var(--color-on-background) / <alpha-value>)",
        "on-surface": "rgb(var(--color-on-surface) / <alpha-value>)",
        "on-surface-variant": "rgb(var(--color-on-surface-variant) / <alpha-value>)",
        outline: "rgb(var(--color-outline) / <alpha-value>)",
        "outline-variant": "rgb(var(--color-outline-variant) / <alpha-value>)",
        primary: "rgb(var(--color-primary) / <alpha-value>)",
        "primary-container": "rgb(var(--color-primary-container) / <alpha-value>)",
        "on-primary-container": "rgb(var(--color-on-primary-container) / <alpha-value>)",
        secondary: "rgb(var(--color-secondary) / <alpha-value>)",
        "secondary-container": "rgb(var(--color-secondary-container) / <alpha-value>)",
        "on-secondary-container": "rgb(var(--color-on-secondary-container) / <alpha-value>)",
        error: "rgb(var(--color-error) / <alpha-value>)",
        success: "rgb(var(--color-success) / <alpha-value>)",
        caution: "rgb(var(--color-caution) / <alpha-value>)",
        danger: "rgb(var(--color-danger) / <alpha-value>)",
        "severity-1": "rgb(var(--severity-1) / <alpha-value>)",
        "severity-2": "rgb(var(--severity-2) / <alpha-value>)",
        "severity-3": "rgb(var(--severity-3) / <alpha-value>)",
        "severity-4": "rgb(var(--severity-4) / <alpha-value>)",
        "severity-5": "rgb(var(--severity-5) / <alpha-value>)"
      },
      fontFamily: {
        display: ["Inter", '"Segoe UI"', "sans-serif"],
        body: ["Inter", '"Segoe UI"', "sans-serif"],
        label: ['"Work Sans"', "Inter", '"Segoe UI"', "sans-serif"],
        data: ['"Work Sans"', "Inter", '"Segoe UI"', "sans-serif"],
        mono: ['"IBM Plex Mono"', '"SFMono-Regular"', "ui-monospace", "monospace"]
      },
      borderRadius: {
        DEFAULT: "0.125rem",
        lg: "0.25rem",
        xl: "0.5rem",
        full: "0.75rem"
      },
      spacing: {
        unit: "4px",
        gutter: "16px",
        "container-padding": "24px",
        "sidebar-width": "260px",
        "header-height": "64px"
      },
      boxShadow: {
        overlay: "0 4px 12px rgba(15, 23, 42, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;
