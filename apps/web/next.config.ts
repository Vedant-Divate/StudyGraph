import type { NextConfig } from "next";

// NOTE: no `output: "standalone"` — standalone tracing needs symlinks, which
// Windows dev machines without Developer Mode cannot create. The Dockerfile
// runs `next start` instead; revisit if image size matters on the Oracle VM.

const nextConfig: NextConfig = {};

export default nextConfig;
