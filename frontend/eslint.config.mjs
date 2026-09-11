import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    files: [
      "src/app/configuracoes/page.tsx",
      "src/app/crm-app/**/page.tsx",
      "src/app/mapa-estrategico/page.tsx",
    ],
    rules: {
      "react-hooks/set-state-in-effect": "off",
    },
  },
  {
    files: [
      "src/app/atividades/page.tsx",
      "src/app/oportunidades/page.tsx",
      "src/app/pedidos/page.tsx",
      "src/app/pipeline/page.tsx",
      "src/app/propostas/page.tsx",
    ],
    rules: {
      "react-hooks/preserve-manual-memoization": "off",
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
