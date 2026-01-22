/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',  // Required for Docker deployment
  experimental: {
    serverActions: true,
  },
}

module.exports = nextConfig
