/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // `swcMinify` was removed as a valid option in Next 15 (SWC minification is
  // always on) and Next 16 warns about it, so it is deliberately absent here.
  //
  // `src/instrumentation.ts` needs no config either: the instrumentation hook
  // graduated from `experimental.instrumentationHook` to stable in Next 15, and
  // re-adding that flag would raise the same kind of unrecognized-option warning.
};

export default nextConfig;
