import nextConfig from "eslint-config-next";
import { fixupConfigRules } from "@eslint/compat";

export default [
  ...fixupConfigRules(nextConfig),
  {
    ignores: [
      ".next/**",
      "out/**",
      "build/**",
      "node_modules/**",
      "next-env.d.ts",
    ],
  },
];
