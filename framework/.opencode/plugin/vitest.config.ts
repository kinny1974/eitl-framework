import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    globals: true,
    environment: "node",
    include: ["**/__tests__/**/*.test.ts"],
    // 04 §7: los tests se ejecutan en orden aleatorio para garantizar que son
    // independientes (order-independent). Los tests ya son state-independent
    // (cada uno limpia/crea su propio estado en mockFiles).
    sequence: {
      shuffle: true,
      seed: 0,
    },
    coverage: {
      reporter: ["text", "json", "html"],
      exclude: ["node_modules/", "__tests__/"],
      // Umbrales del Gate 4 (≥ 80%): hacen fallar `npm run test:coverage` en la CI
      // si la cobertura baja. Valores reales de la línea base 1.0b: 99% stmts /
      // 91.5% ramas / 100% funcs / 100% lines.
      thresholds: {
        statements: 80,
        branches: 80,
        functions: 80,
        lines: 80,
      },
    },
  },
});
