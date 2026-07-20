/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "system-ui", "sans-serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      colors: {
        milk: {
          DEFAULT: "#FAF9F5",
          100: "#FFFFFF",
          200: "#F5F3EC",
          300: "#EDEAE0",
        },
        ink: {
          DEFAULT: "#1C1B2E",
          light: "#4B4A66",
          faint: "#8886A3",
        },
      },
      boxShadow: {
        card: "0 1px 2px rgba(28, 27, 46, 0.04), 0 8px 24px -12px rgba(28, 27, 46, 0.10)",
      },
      animation: {
        "fade-in": "fadeIn 0.35s ease-out",
        "slide-up": "slideUp 0.4s ease-out",
      },
      keyframes: {
        fadeIn: { "0%": { opacity: 0 }, "100%": { opacity: 1 } },
        slideUp: {
          "0%": { opacity: 0, transform: "translateY(12px)" },
          "100%": { opacity: 1, transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
