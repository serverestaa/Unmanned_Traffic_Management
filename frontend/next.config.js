/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    experimental: {
      serverComponentsExternalPackages: ['leaflet']
    },
    webpack: (config, { isServer }) => {
      if (!isServer) {
        config.resolve.fallback = {
          ...config.resolve.fallback,
          fs: false,
        };
      }
      return config;
    },
  }
  
  module.exports = nextConfig