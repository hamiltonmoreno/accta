/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,jsx}',
    './components/**/*.{js,jsx}',
    './app/**/*.{js,jsx}',
    './src/**/*.{js,jsx}',
  ],
  prefix: "",
  theme: {
    screens: {
      'xs': '360px',
      'sm': '640px',
      'md': '768px',
      'lg': '1024px',
      'xl': '1280px',
      '2xl': '1536px',
    },
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        // ACCTA Brand Colors
        primary: {
          DEFAULT: "#3A3A3A",
          foreground: "#FFFFFF",
        },
        secondary: {
          DEFAULT: "#F5F5F5",
          foreground: "#3A3A3A",
        },
        accent: {
          DEFAULT: "#F5F5F5",
          foreground: "#3A3A3A",
        },
        carmesim: {
          DEFAULT: "#C7202F",
          light: "#E8444F",
          dark: "#A51B27",
          50: "#FEF2F2",
          100: "#FEE2E4",
        },
        grafite: {
          DEFAULT: "#3A3A3A",
          light: "#5A5A5A",
          dark: "#2A2A2A",
          50: "#F7F7F7",
        },
        // Ação primária positiva (Guardar/Aprovar/Submeter…). Carmesim continua
        // a ser identidade de marca + destrutivo. Ver tasks/spec-botoes-cor-acao.md.
        floresta: {
          DEFAULT: "#166534", // verde-800; 6.2:1 com texto branco (AA)
          dark: "#14532D",    // hover
          50: "#F0FDF4",      // tint (badges de sucesso podem reutilizar)
        },
        alert: {
          DEFAULT: "#C7202F",
          foreground: "#FFFFFF",
        },
        destructive: {
          DEFAULT: "#C7202F",
          foreground: "#FFFFFF",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      spacing: {
        // Altura da navbar pública fixa — usada no padding-top do <main>.
        navbar: '60px',
      },
      fontFamily: {
        sans: ['Open Sans', 'sans-serif'],
        heading: ['Open Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        // Substitutos CSS para os <motion.div initial/animate> mais comuns —
        // permite remover framer-motion de paginas estaticas sem perder o efeito.
        "fade-up": {
          from: { opacity: "0", transform: "translateY(20px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        // Exit-side keyframes para componentes always-mounted que usam
        // data-state ou condicional className para fade-out antes de hide.
        "fade-out": {
          from: { opacity: "1", transform: "translateY(0) scale(1)" },
          to: { opacity: "0", transform: "translateY(-8px) scale(0.97)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "fade-up": "fade-up 0.3s cubic-bezier(0.32, 0.72, 0, 1) both",
        "fade-in": "fade-in 0.3s ease-out both",
        "fade-out": "fade-out 0.18s cubic-bezier(0.32, 0.72, 0, 1) both",
      },
      // Curva de easing tipo "spring" (Apple-like) — usar via ease-spring em
      // transitions Tailwind. Mais polish que ease-out linear.
      transitionTimingFunction: {
        spring: "cubic-bezier(0.32, 0.72, 0, 1)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
