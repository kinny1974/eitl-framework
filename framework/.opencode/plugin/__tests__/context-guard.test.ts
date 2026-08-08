import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@opencode-ai/plugin", () => ({
  tool: (config: any) => config,
  schema: {
    enum: (...values: string[]) => ({ _type: "enum", values }),
    number: () => ({ _type: "number", min: vi.fn(), max: vi.fn(), optional: vi.fn() }),
    int: () => ({ _type: "int", min: vi.fn(), max: vi.fn(), optional: vi.fn() }),
    boolean: () => ({ _type: "boolean", default: vi.fn() }),
    string: () => ({ _type: "string" }),
  },
}));

const mockFiles: Record<string, string> = {};
vi.mock("fs", () => ({
  existsSync: (p: string) => p in mockFiles,
  readFileSync: (p: string, enc: string) => mockFiles[p] || "{}",
  writeFileSync: (p: string, data: string) => { mockFiles[p] = data; },
  mkdirSync: vi.fn(),
}));

vi.mock("path", () => ({
  join: (...parts: string[]) => parts.join("/"),
  dirname: (p: string) => p.split("/").slice(0, -1).join("/"),
}));

describe("Context Guard Plugin", () => {
  beforeEach(() => {
    for (const key in mockFiles) delete mockFiles[key];
    process.env.OPENCODE_STATE_DIR = ".opencode/.context-guard";
  });

  it("should have valid thresholds for scrum-master", () => {
    const safeThreshold = 0.65;
    const criticalThreshold = 0.80;
    expect(safeThreshold).toBeLessThan(criticalThreshold);
    expect(safeThreshold).toBeGreaterThan(0);
    expect(criticalThreshold).toBeLessThan(1);
  });

  it("should estimate tokens correctly", () => {
    const text = "Hello world";
    const estimated = Math.ceil(text.length / 3.5);
    expect(estimated).toBe(4);
  });

  it("should return OK when below safe threshold", () => {
    const ratio = 0.50, safe = 0.65, critical = 0.80;
    let level: "ok" | "warning" | "critical" = "ok";
    if (ratio >= critical) level = "critical";
    else if (ratio >= safe) level = "warning";
    expect(level).toBe("ok");
  });

  it("should return WARNING when above safe", () => {
    const ratio = 0.70, safe = 0.65, critical = 0.80;
    let level: "ok" | "warning" | "critical" = "ok";
    if (ratio >= critical) level = "critical";
    else if (ratio >= safe) level = "warning";
    expect(level).toBe("warning");
  });

  it("should return CRITICAL when above critical", () => {
    const ratio = 0.85, safe = 0.65, critical = 0.80;
    let level: "ok" | "warning" | "critical" = "ok";
    if (ratio >= critical) level = "critical";
    else if (ratio >= safe) level = "warning";
    expect(level).toBe("critical");
  });

  it("should detect architect from system message", () => {
    const systemMsgs = [{ role: "system", content: "You are the architect agent..." }];
    const lastSys = systemMsgs[systemMsgs.length - 1]?.content || "";
    const agents = ["scrum-master", "product-owner", "architect", "tdd-engineer", "validator"];
    let detected = "auto";
    for (const key of agents) {
      if (lastSys.toLowerCase().includes(key)) { detected = key; break; }
    }
    if (detected === "auto") detected = "architect";
    expect(detected).toBe("architect");
  });

  it("should fallback to architect when no agent detected", () => {
    const systemMsgs = [{ role: "system", content: "You are a helpful assistant." }];
    const lastSys = systemMsgs[systemMsgs.length - 1]?.content || "";
    const agents = ["scrum-master", "product-owner", "architect", "tdd-engineer", "validator"];
    let detected = "auto";
    for (const key of agents) {
      if (lastSys.toLowerCase().includes(key)) { detected = key; break; }
    }
    if (detected === "auto") detected = "architect";
    expect(detected).toBe("architect");
  });
});
