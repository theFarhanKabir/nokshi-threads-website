import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  turbopack: { root: process.cwd() },
  async rewrites() {
    const apiOrigin = process.env.API_BACKEND_URL || 'http://127.0.0.1:4001';
    return [{ source: '/api/:path*', destination: `${apiOrigin}/api/:path*` }];
  },
};

export default nextConfig;
