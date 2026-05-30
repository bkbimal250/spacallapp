/** @type {import('tailwindcss').Config} */

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],

  theme: {
    extend: {

      colors: {

        primary: "rgb(var(--primary) / <alpha-value>)",
        primarySoft: "rgb(var(--primary-soft) / <alpha-value>)",

        background: "rgb(var(--background) / <alpha-value>)",
        surface: "rgb(var(--surface) / <alpha-value>)",
        card: "rgb(var(--card-bg) / <alpha-value>)",
        cardHover: "rgb(var(--surface-hover) / <alpha-value>)",

        sidebar: "rgb(var(--sidebar-bg) / <alpha-value>)",
        sidebarHover: "rgb(var(--sidebar-hover) / <alpha-value>)",

        borderColor: "rgb(var(--border) / <alpha-value>)",
        border: "rgb(var(--border) / <alpha-value>)",

        textPrimary:
          "rgb(var(--text-primary) / <alpha-value>)",

        textSecondary:
          "rgb(var(--text-secondary) / <alpha-value>)",

        textMuted:
          "rgb(var(--text-muted) / <alpha-value>)",

        success:
          "rgb(var(--success) / <alpha-value>)",

        warning:
          "rgb(var(--warning) / <alpha-value>)",

        danger:
          "rgb(var(--danger) / <alpha-value>)",

        info:
          "rgb(var(--info) / <alpha-value>)",
      },

      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
      },

      boxShadow: {
        soft: "var(--shadow-sm)",
        medium: "var(--shadow-md)",
        large: "var(--shadow-lg)",
      },
    },
  },

  plugins: [],
};
