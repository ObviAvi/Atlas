/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        sand: {
          50: '#FAF8F5',
          100: '#F3EFE8',
          200: '#E8E2D8',
          300: '#D4C9BA',
        },
        walnut: {
          400: '#8B7355',
          500: '#6B4E3D',
          600: '#5A4032',
          700: '#3D2B1F',
          800: '#2A1E16',
          900: '#1A1612',
        },
        cream: '#F5F1EB',
      },
      fontFamily: {
        display: ['var(--font-display)', 'Georgia', 'serif'],
        body: ['var(--font-body)', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        '4xl': '2rem',
      },
      boxShadow: {
        float: '0 24px 64px -12px rgba(26, 22, 18, 0.18)',
        card: '0 8px 32px -8px rgba(26, 22, 18, 0.12)',
      },
      animation: {
        'fade-up': 'fadeUp 0.7s ease-out forwards',
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'debate-slide-left': 'debateSlideLeft 0.45s ease-out forwards',
        'debate-slide-right': 'debateSlideRight 0.45s ease-out forwards',
        'debate-pulse': 'debatePulse 1.6s ease-in-out infinite',
        'debate-bounce': 'debateBounce 0.6s ease-in-out infinite',
      },
      keyframes: {
        fadeUp: {
          '0%': { opacity: '0', transform: 'translateY(24px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        debateSlideLeft: {
          '0%': { opacity: '0', transform: 'translateX(-28px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        debateSlideRight: {
          '0%': { opacity: '0', transform: 'translateX(28px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        debatePulse: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(107, 78, 61, 0.25)' },
          '50%': { boxShadow: '0 0 0 10px rgba(107, 78, 61, 0)' },
        },
        debateBounce: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-4px)' },
        },
      },
    },
  },
  plugins: [],
}

// Made with Bob
