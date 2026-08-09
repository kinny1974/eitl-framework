import { describe, expect, it, vi } from "vitest";

const { mockFiles } = vi.hoisted(() => ({ mockFiles: {} as Record<string, string> }));

vi.mock("@opencode-ai/plugin", () => {
  const makeDef = (type: string) => {
    const def: any = { _type: type };
    const set = (key: string) => (value: any) => {
      def[key] = value === undefined ? true : value;
      return def;
    };
    def.min = set("min");
    def.max = set("max");
    def.optional = set("optional");
    def.int = set("int");
    def.default = set("default");
    def.describe = set("describe");
    return def;
  };
  const toolFn: any = (config: any) => config;
  toolFn.schema = {
    enum: () => makeDef("enum"),
    number: () => makeDef("number"),
    boolean: () => makeDef("boolean"),
    string: () => makeDef("string"),
  };
  return { tool: toolFn };
});

vi.mock("fs", () => ({
  existsSync: (p: string) => p in mockFiles,
  readFileSync: (p: string) => mockFiles[p] || "{}",
  writeFileSync: (p: string, data: string) => {
    mockFiles[p] = data;
  },
  mkdirSync: () => undefined,
  // submódulo promises: el plugin usa fs.promises (E/S asíncrona, B2)
  promises: {
    readFile: async (p: string) => {
      if (!(p in mockFiles)) throw new Error("ENOENT");
      return mockFiles[p];
    },
    writeFile: async (p: string, data: string) => {
      mockFiles[p] = data;
    },
    mkdir: async () => undefined,
  },
}));

vi.mock("path", () => ({
  join: (...parts: string[]) => parts.join("/"),
  dirname: (p: string) => p.split("/").slice(0, -1).join("/"),
}));

import plugin from "../context-guard";

describe("Batch stress / métricas de memoria (plugin real)", () => {
  it(
    "ejecuta 2,000 checks en lote y mide rendimiento y memoria",
    async () => {
      process.env.OPENCODE_STATE_DIR = ".opencode/.context-guard";
      const ctx = {
        sessionID: "stress",
        session: {
          messages: [{ role: "user", content: "Build a REST API" }],
          tokenUsage: { total: 64000, prompt: 40000, completion: 24000 },
          contextLimit: 128000,
        },
      };

      if (typeof globalThis.gc === "function") globalThis.gc();

      const memBefore = process.memoryUsage();
      const t0 = performance.now();

      for (let i = 0; i < 2000; i++) {
        await plugin.execute({ action: "check", agent: "architect" }, ctx as any);
      }

      const elapsed = performance.now() - t0;
      const memAfter = process.memoryUsage();
      const rssDeltaMB = (memAfter.rss - memBefore.rss) / 1024 / 1024;
      const heapDeltaMB = (memAfter.heapUsed - memBefore.heapUsed) / 1024 / 1024;
      const opsPerSec = Math.round(2000 / (elapsed / 1000));

      // eslint-disable-next-line no-console
      console.log(`[PERF] 2,000 checks en ${elapsed.toFixed(0)} ms → ${opsPerSec.toLocaleString()} ops/s`);
      // eslint-disable-next-line no-console
      console.log(`[PERF] RSS Δ: ${rssDeltaMB.toFixed(1)} MB | heapUsed Δ: ${heapDeltaMB.toFixed(1)} MB`);

      // sanity: no debería tardar más de 60s
      expect(elapsed).toBeLessThan(60000);
    },
    120000
  );
});
