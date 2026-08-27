// Flat config: `next lint` was removed in Next 16, so ESLint is invoked
// directly (see the `lint` script). There was no config file before this,
// which meant the lint script had nothing to enforce.
import next from "eslint-config-next";
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypescript from "eslint-config-next/typescript";

const config = [
  { ignores: [".next/**", "node_modules/**", "src/lib/contracts.generated.ts"] },
  ...next,
  ...nextCoreWebVitals,
  ...nextTypescript,
];

export default config;
