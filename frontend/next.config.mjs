/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  // Hide the dev-only "N" route/insight pill that overlaps the sidebar; build and
  // runtime errors still show their overlay.
  devIndicators: false,
}

export default nextConfig
