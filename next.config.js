/** @type {import('next').NextConfig} */
const backendApi = process.env.NEXT_PUBLIC_API_URL || 'https://ops.theboostnation.com/api/goldrix'

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

