import type { NextConfig } from "next";

const api = process.env.CARRERA_API_URL ?? "http://127.0.0.1:8920";

const nextConfig: NextConfig = {
  // The browser only talks to this app; the Python API stays on localhost.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${api}/api/:path*` }];
  },
};

export default nextConfig;
