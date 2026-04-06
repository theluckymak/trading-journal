/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#3AA8FC',
          light: 'rgba(58,168,252,0.1)',
          hover: '#2D96E8',
          dark: '#1E7FCC',
        },
        surface: {
          DEFAULT: '#FFFFFF',
          section: '#E8E8E8',
          dark: '#212121',
          'dark-card': '#2C2C2C',
          'dark-elevated': '#333333',
        },
        text: {
          DEFAULT: '#1A1A1A',
          muted: '#8E8E93',
          dark: '#FFFFFF',
          'dark-muted': '#8E8E93',
        },
        border: {
          DEFAULT: '#D5D5D5',
          dark: '#3A3A3A',
        },
        success: '#29CC6A',
        error: '#FF2D55',
        warning: '#F5A623',
      },
      borderRadius: {
        'card': '26px',
        'btn': '19px',
        'input': '12px',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
