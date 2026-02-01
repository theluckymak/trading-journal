/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    // For Railway: Set NEXT_PUBLIC_API_URL in environment variables
    // Default to your Railway backend URL
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://trading-journal-backend.railway.app',
  },
}

module.exports = nextConfig

