import { afterAll, beforeAll, bench, describe, vi } from "vitest";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

// Mock del API @opencode-ai/plugin (el plugin se ejecuta con lógica real).
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

import plugin from "./context-guard.js";

const TMP_DIR = fs.mkdtempSync(path.join(os.tmpdir(), "eitl-bench-"));
const LIMIT = 128000;

function makeSession(overrides: Record<string, any> = {}) {
  return {
    messages: [
      { role: "user", content: "Build a REST API" },
      { role: "assistant", content: "Here is the plan..." },
      { role: "system", content: "You are the architect agent. Design before code." },
    ],
    tokenUsage: { total: 64000, prompt: 40000, completion: 24000 },
    contextLimit: LIMIT,
    ...overrides,
  };
}

const baseCtx = {
  sessionID: "bench-session",
  session: makeSession(),
};

const REPORT_STATE = {
  alertsSent: Array.from({ length: 10 }, (_, i) => ({
    level: "warning" as const,
    percent: 60,
    tokens: 76800,
    agent: "architect",
    at: new Date().toISOString(),
  })),
  lastCompaction: new Date().toISOString(),
  agentSwitches: Array.from({ length: 10 }, (_, i) => ({
    from: `agent-${i}`,
    to: `agent-${i + 1}`,
    at: new Date().toISOString(),
    tokensAtSwitch: 64000,
  })),
};

beforeAll(() => {
  process.env.OPENCODE_STATE_DIR = TMP_DIR;
  // sembrar el estado fuera del callback medido (report no escribe estado)
  fs.writeFileSync(path.join(TMP_DIR, "bench-report.json"), JSON.stringify(REPORT_STATE));
});

afterAll(() => {
  fs.rmSync(TMP_DIR, { recursive: true, force: true });
});

describe("context-guard · latencia por acción (fs real en tmpdir)", () => {
  bench("check · healthy (50% de contexto)", async () => {
    await plugin.execute({ action: "check", agent: "architect", dryRun: false }, baseCtx as any);
  });

  bench("check · estimación de tokens con 100 KB de mensajes", async () => {
    const big = "x".repeat(100_000);
    const ctx = {
      sessionID: "bench-big",
      session: makeSession({ tokenUsage: { total: 0, prompt: 0, completion: 0 }, messages: [{ role: "user", content: big }] }),
    };
    await plugin.execute({ action: "check", agent: "architect", dryRun: false }, ctx as any);
  });

  bench("report · con 10 alertas y 10 switches acumulados", async () => {
    const ctx = { sessionID: "bench-report", session: makeSession() };
    await plugin.execute({ action: "report", agent: "architect", dryRun: false }, ctx as any);
  });

  bench("switch-agent · persistencia de estado (escritura)", async () => {
    await plugin.execute({ action: "switch-agent", agent: "scrum-master", dryRun: false }, baseCtx as any);
  });

  bench("compact · dry-run", async () => {
    await plugin.execute({ action: "compact", agent: "architect", dryRun: true }, baseCtx as any);
  });

  bench("set-threshold · ajuste de umbral", async () => {
    await plugin.execute({ action: "set-threshold", agent: "architect", thresholdOverride: 0.9, dryRun: false }, baseCtx as any);
  });
});
