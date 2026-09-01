/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // better-sqlite3 is a native addon: bundling it produces an invalid-ELF /
  // module-not-found failure at runtime. It must stay external.
  serverExternalPackages: ["better-sqlite3"],

  // `X-Powered-By: Next.js` names the framework on every response. It buys
  // nothing and it is the one header in the set that vercel.json cannot remove,
  // so it is turned off at the source. Consistent with the rest of the header
  // policy there.
  poweredByHeader: false,

  // Both are barrel files: an unqualified `import { Activity } from
  // "lucide-react"` pulls the whole index into the module graph, and the same
  // goes for recharts. Next rewrites those to per-module imports, which is
  // worth a large fraction of this app's client bundle — the icons alone are
  // imported from a dozen components.
  //
  // lucide-react is on Next's built-in list already; recharts is not, and it is
  // the bigger of the two. Naming both keeps the optimisation explicit rather
  // than dependent on a default that can change between minors.
  experimental: {
    optimizePackageImports: ["lucide-react", "recharts"],
  },
};

export default nextConfig;
