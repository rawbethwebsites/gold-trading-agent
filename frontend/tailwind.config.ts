import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: '#0f1012',
        surface: '#17181b',
        'surface-2': '#1d1f23',
        'surface-3': '#23262b',
        border: 'rgba(255,255,255,0.07)',
        grid: 'rgba(255,255,255,0.04)',
        text: '#f1f3f5',
        muted: '#a2a9b3',
        faint: '#6b7280',
        green: '#58d17a',
        red: '#ff6d8c',
        gold: '#f0c36b',
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'Inter', 'sans-serif'],
        mono: ['var(--font-mono)', 'IBM Plex Mono', 'monospace'],
      },
      borderRadius: {
        xl: '18px',
        lg: '14px',
        md: '10px',
      },
    },
  },
  plugins: [],
}

export default config
