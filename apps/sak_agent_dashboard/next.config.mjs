/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // better-sqlite3 is a native addon: bundling it produces an invalid-ELF /
  // module-not-found failure at runtime. It must stay external.
  serverExternalPackages: ["better-sqlite3"],
};

export default nextConfig;
