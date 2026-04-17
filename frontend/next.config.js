/** @type {import('next').NextConfig} */
const backendApi = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api/goldrix'

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendApi.replace(/\/$/, '')}/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
