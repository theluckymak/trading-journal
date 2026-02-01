/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    // Railway backend service: dependable-solace
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://dependable-solace-production-75f7.up.railway.app',
  },
}

module.exports = nextConfig

