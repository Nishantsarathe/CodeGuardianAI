/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  experimental: {
    serverActions: { bodySizeLimit: "10mb" },
  },
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      { source: "/api/backend/:path*", destination: `${apiUrl}/api/v1/:path*` },
      { source: "/api/health", destination: `${apiUrl}/health` },
    ];
  },
};
export default nextConfig;
