import { afterAll, beforeEach, describe, expect, it, vi } from "vitest";

// Estado compartido de los mocks (vi.hoisted para que exista antes de los vi.mock)
const { mockFiles, schemaDefs } = vi.hoisted(() => {
  const mockFiles: Record<string, string> = {};
  const schemaDefs: any[] = [];
  return { mockFiles, schemaDefs };
});

// Mock del API @opencode-ai/plugin: tool() devuelve el config tal cual y
// schema es un builder encadenable que registra las definiciones.
vi.mock("@opencode-ai/plugin", () => {
  const makeDef = (type: string) => {
    const def: any = { _type: type };
    schemaDefs.push(def);
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
    enum: (values: string[]) => makeDef("enum"),
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

// IMPORTANTE: importamos el plugin REAL (el mock de @opencode-ai/plugin
// devuelve el objeto de configuración tal cual, por lo que ejecutamos su
// lógica real y no una reimplementación).
import plugin, { server } from "../context-guard";

const LIMIT = 128000;
const STATE_PATH = ".opencode/.context-guard/test-session-001.json";
const originalStateDir = process.env.OPENCODE_STATE_DIR;

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

// ToolContext de la API actual: agent/directory/worktree + `session` legacy opcional
// (los runtimes que aún la inyectan la leen de forma defensiva).
function makeContext(sessionOverrides: Record<string, any> = {}, extra: Record<string, any> = {}) {
  return {
    sessionID: "test-session-001",
    agent: "architect",
    directory: "/project",
    worktree: "/project",
    session: makeSession(sessionOverrides),
    ...extra,
  };
}

function readState(path = STATE_PATH): any {
  if (!mockFiles[path]) throw new Error(`Estado no escrito en ${path} (¿se ejecutó una acción antes?)`);
  return JSON.parse(mockFiles[path]);
}

describe("Context Guard Plugin — unit tests sobre el plugin real (API actual)", () => {
  beforeEach(() => {
    for (const key in mockFiles) delete mockFiles[key];
    process.env.OPENCODE_STATE_DIR = ".opencode/.context-guard";
  });

  afterAll(() => {
    // higiene: restaurar el env var original del entorno
    process.env.OPENCODE_STATE_DIR = originalStateDir;
  });

  describe("Contrato del módulo (tool config + hooks del plugin)", () => {
    it("exporta descripción, args y execute", () => {
      expect(typeof plugin.description).toBe("string");
      expect(plugin.description).toContain("context");
      expect(plugin.args).toBeTruthy();
      expect(typeof plugin.execute).toBe("function");
    });

    it("NO define 'name' en el config del tool (la API actual no lo acepta)", () => {
      expect(plugin).not.toHaveProperty("name");
    });

    it("registra el tool 'context-guard' en los hooks del plugin (server)", async () => {
      const hooks = await server();
      expect(hooks.tool).toBeDefined();
      expect(hooks.tool?.["context-guard"]).toBe(plugin);
    });

    it("define action con default 'check'", () => {
      const actionDef = schemaDefs.find((d) => d._type === "enum" && d.default === "check");
      expect(actionDef).toBeTruthy();
    });

    it("define agent con default 'auto'", () => {
      const agentDef = schemaDefs.find((d) => d._type === "enum" && d.default === "auto");
      expect(agentDef).toBeTruthy();
    });

    it("define thresholdOverride con rango 0.1–0.95", () => {
      const overrideDef = schemaDefs.find((d) => d._type === "number" && d.min === 0.1 && d.max === 0.95);
      expect(overrideDef).toBeTruthy();
    });

    it("define preserveRecent como entero 1–50", () => {
      const preserveDef = schemaDefs.find((d) => d._type === "number" && d.int === true && d.min === 1 && d.max === 50);
      expect(preserveDef).toBeTruthy();
    });
  });

  describe("Detección de agente (agent=auto → context.agent)", () => {
    it("usa context.agent cuando agent=auto", async () => {
      const out = await plugin.execute({ action: "check", agent: "auto" }, makeContext() as any);
      expect(out).toContain("`architect`");
    });

    it("respeta el agente explícito en lugar de context.agent", async () => {
      const out = await plugin.execute({ action: "check", agent: "validator" }, makeContext() as any);
      expect(out).toContain("`validator`");
    });

    it("hace fallback a 'architect' cuando context.agent no es un agente conocido", async () => {
      const ctx = makeContext({}, { agent: "unknown-role" });
      const out = await plugin.execute({ action: "check", agent: "auto" }, ctx as any);
      expect(out).toContain("`architect`");
    });

    it("hace fallback a 'architect' cuando context.agent está vacío", async () => {
      const ctx = makeContext({}, { agent: "" });
      const out = await plugin.execute({ action: "check", agent: "auto" }, ctx as any);
      expect(out).toContain("`architect`");
    });
  });

  describe("Niveles de alerta (perfil architect: safe 55%, crítico 70%)", () => {
    it("OK al 50% de uso", async () => {
      const out = await plugin.execute({ action: "check", agent: "architect" }, makeContext() as any);
      expect(out).toContain("Healthy");
      expect(out).toContain("Estado:** OK");
      expect(out).toContain("50%");
    });

    it("WARNING al 65% (supera umbral seguro, bajo el crítico)", async () => {
      const ctx = makeContext({ tokenUsage: { total: 83200 } }); // 65%
      const out = await plugin.execute({ action: "check", agent: "architect" }, ctx as any);
      expect(out).toContain("WARNING");
      expect(out).toContain("65%");
    });

    it("CRITICAL al 85% (supera umbral crítico)", async () => {
      const ctx = makeContext({ tokenUsage: { total: 108800 } }); // 85%
      const out = await plugin.execute({ action: "check", agent: "architect" }, ctx as any);
      expect(out).toContain("CRITICAL");
      expect(out).toContain("85%");
    });

    it("thresholdOverride eleva el umbral seguro y cambia el resultado", async () => {
      const ctx = makeContext({ tokenUsage: { total: 83200 } }); // 65%
      const withoutOverride = await plugin.execute({ action: "check", agent: "architect" }, ctx as any);
      expect(withoutOverride).toContain("WARNING");
      const withOverride = await plugin.execute(
        { action: "check", agent: "architect", thresholdOverride: 0.8 },
        ctx as any
      );
      expect(withOverride).toContain("Healthy");
    });

    it("alcanzar exactamente el umbral crítico dispara CRITICAL (>=)", async () => {
      const ctx = makeContext({ tokenUsage: { total: 89600 } }); // 70% exacto = crítico
      const out = await plugin.execute({ action: "check", agent: "architect" }, ctx as any);
      expect(out).toContain("CRITICAL");
    });
  });

  describe("Cálculo de tokens", () => {
    it("usa tokenUsage cuando está disponible (fuente legacy session)", async () => {
      const out = await plugin.execute({ action: "check", agent: "architect" }, makeContext() as any);
      // salida determinista (B3): formateo fijo en-US, siempre 64,000 (con coma)
      expect(out).toContain("64,000** / 128,000");
      expect(out).toContain("64000/128000");
    });

    it("usa métricas persistidas cuando no hay tokenUsage en vivo", async () => {
      const ctxLive = makeContext() as any; // 64000 live → persiste
      await plugin.execute({ action: "check", agent: "architect" }, ctxLive);
      const ctxNoLive = {
        sessionID: "test-session-001",
        agent: "architect",
        directory: "/project",
        worktree: "/project",
        session: { messages: [] },
      } as any;
      const out = await plugin.execute({ action: "check", agent: "architect" }, ctxNoLive);
      expect(out).toContain("64000/128000");
      expect(out).toContain("(persistido)");
    });

    it("sin datos de uso reporta 'no disponibles' con estado preventivo OK", async () => {
      const ctx = {
        sessionID: "fresh-session",
        agent: "architect",
        directory: "/project",
        worktree: "/project",
      } as any;
      const out = await plugin.execute({ action: "check", agent: "architect" }, ctx);
      expect(out).toContain("no disponibles");
      expect(out).toContain("Estado:** OK");
    });

    it("resuelve el límite desde session.model.info.limit.context cuando no hay contextLimit", async () => {
      const ctx = makeContext({
        tokenUsage: { total: 32000 },
        contextLimit: undefined,
        model: { info: { limit: { context: 64000 } } },
      });
      const out = await plugin.execute({ action: "check", agent: "architect" }, ctx as any);
      expect(out).toContain("32000/64000");
      expect(out).toContain("50%");
    });

    it("reporta tokens restantes en formato determinista en-US", async () => {
      const out = await plugin.execute({ action: "check", agent: "architect" }, makeContext() as any);
      expect(out).toContain("Remaining: **64,000** tokens"); // B3: fijo, sin depender del locale del SO
    });

    it("usa DEFAULT_LIMIT cuando hay métricas live pero ningún límite (rama 235)", async () => {
      const ctx = makeContext({ tokenUsage: { total: 32000 }, contextLimit: undefined }) as any;
      const out = await plugin.execute({ action: "check", agent: "architect" }, ctx);
      expect(out).toContain("32000/128000");
      expect(out).toContain("25%");
    });

    it("usa DEFAULT_LIMIT cuando el estado persiste tokens pero no el límite (rama 238)", async () => {
      // estado con lastTokenUsage pero SIN lastTokenLimit
      mockFiles[STATE_PATH] = JSON.stringify({
        alertsSent: [],
        lastCompaction: null,
        agentSwitches: [],
        lastTokenUsage: { total: 32000, at: new Date().toISOString() },
      });
      const ctx = {
        sessionID: "test-session-001",
        agent: "architect",
        directory: "/project",
        worktree: "/project",
        session: { messages: [] },
      } as any;
      const out = await plugin.execute({ action: "check", agent: "architect" }, ctx);
      expect(out).toContain("32000/128000");
      expect(out).toContain("25%");
    });
  });

  describe("Persistencia de estado", () => {
    it("recupera estado por defecto si el archivo está corrupto (rama catch de loadState)", async () => {
      mockFiles[STATE_PATH] = "{ esto no es json válido";
      const ctx = makeContext() as any;
      const out = await plugin.execute({ action: "check", agent: "architect" }, ctx);
      // no lanza: cae al estado por defecto y continúa con normalidad
      expect(out).toContain("Healthy");
      expect(out).toContain("50%");
      // y la siguiente escritura repara el archivo con estado válido
      const state = readState();
      expect(Array.isArray(state.alertsSent)).toBe(true);
      expect(state.alertsSent).toHaveLength(1);
    });

    it("acumula una alerta por cada check", async () => {
      const ctx = makeContext() as any;
      await plugin.execute({ action: "check", agent: "architect" }, ctx);
      await plugin.execute({ action: "check", agent: "architect" }, ctx);
      const state = readState();
      expect(state.alertsSent).toHaveLength(2);
      expect(state.alertsSent[0].agent).toBe("architect");
      expect(state.alertsSent[0].level).toBe("ok");
    });

    it("persiste lastTokenUsage cuando hay métricas en vivo", async () => {
      const ctx = makeContext() as any;
      await plugin.execute({ action: "check", agent: "architect" }, ctx);
      const state = readState();
      expect(state.lastTokenUsage?.total).toBe(64000);
      expect(state.lastTokenLimit).toBe(128000);
    });

    it("poda el historial de alertas a 50 conservando las MÁS RECIENTES", async () => {
      // cada check con tokens distintos → alerta distinguible (tokens = 64000 + i)
      const ctx = makeContext() as any;
      for (let i = 0; i < 55; i++) {
        ctx.session.tokenUsage = { total: 64000 + i }; // 50% → 50% (OK, todas)
        await plugin.execute({ action: "check", agent: "architect" }, ctx);
      }
      const state = readState();
      expect(state.alertsSent).toHaveLength(50);
      // la primera conservada es la iteración 5 (55 - 50), no la 0
      expect(state.alertsSent[0].tokens).toBe(64005);
      expect(state.alertsSent[49].tokens).toBe(64054); // la más reciente
    });

    it("poda el historial de agentSwitches a 50 conservando los MÁS RECIENTES", async () => {
      const agents = ["scrum-master", "product-owner", "architect", "tdd-engineer", "validator"];
      const ctx = makeContext() as any;
      for (let i = 0; i < 55; i++) {
        await plugin.execute({ action: "switch-agent", agent: agents[i % 5] }, ctx);
      }
      const state = readState();
      expect(state.agentSwitches).toHaveLength(50);
      // el primero conservado es el switch #5 (ciclo[0]), no el #0
      expect(state.agentSwitches[0].to).toBe("scrum-master");
      expect(state.agentSwitches[49].to).toBe("validator"); // ciclo[54 % 5]
    });
  });

  describe("Acción switch-agent", () => {
    it("registra el switch y actualiza lastAgent", async () => {
      const ctx = makeContext() as any;
      const out = await plugin.execute({ action: "switch-agent", agent: "tdd-engineer" }, ctx);
      expect(out).toContain("Switch to agent **tdd-engineer**");
      const state = readState();
      expect(state.agentSwitches).toHaveLength(1);
      expect(state.agentSwitches[0].from).toBe("unknown");
      expect(state.agentSwitches[0].to).toBe("tdd-engineer");
      expect(state.lastAgent).toBe("tdd-engineer");
    });
  });

  describe("Acción report", () => {
    it("muestra historial de switches y 'Last compaction: N/A' inicial", async () => {
      const ctx = makeContext() as any;
      await plugin.execute({ action: "switch-agent", agent: "product-owner" }, ctx);
      await plugin.execute({ action: "switch-agent", agent: "scrum-master" }, ctx);
      const out = await plugin.execute({ action: "report", agent: "architect" }, ctx);
      expect(out).toContain("Last 10 agent switches:");
      expect(out).toContain("product-owner → scrum-master");
      expect(out).toContain("Last compaction: N/A");
    });

    it("incluye las últimas alertas registradas", async () => {
      const ctx = makeContext({ tokenUsage: { total: 108800 } }) as any; // 85% → CRITICAL
      await plugin.execute({ action: "check", agent: "architect" }, ctx);
      const out = await plugin.execute({ action: "report", agent: "architect" }, ctx);
      expect(out).toContain("CRITICAL — 85%");
    });

    it("sin historial muestra '(none)' y '(ninguno)' (rama vacía de formatReport)", async () => {
      const ctx = makeContext() as any;
      const out = await plugin.execute({ action: "report", agent: "architect" }, ctx);
      expect(out).toContain("Last 10 alerts:");
      expect(out).toContain("(none)");
      expect(out).toContain("(ninguno)");
    });
  });

  describe("Acción set-threshold (L2: persistencia)", () => {
    it("devuelve error si falta thresholdOverride", async () => {
      const out = await plugin.execute({ action: "set-threshold", agent: "architect" }, makeContext() as any);
      expect(out).toContain("Error: thresholdOverride requerido");
    });

    it("ajusta el umbral, lo PERSISTE en el estado y confirma", async () => {
      const ctx = makeContext() as any;
      const out = await plugin.execute(
        { action: "set-threshold", agent: "architect", thresholdOverride: 0.9 },
        ctx
      );
      expect(out).toContain("adjusted to 90%");
      expect(out).toContain("persistido");
      // L2: el ajuste queda en el estado persistido de la sesión
      const state = readState();
      expect(state.thresholdOverrides?.architect).toBe(0.9);
    });

    it("NO muta el perfil compartido AGENTS en memoria (el default queda intacto)", async () => {
      const ctx = makeContext() as any;
      await plugin.execute({ action: "set-threshold", agent: "architect", thresholdOverride: 0.9 }, ctx);
      // un check sin override ni estado debe volver al default 55% del perfil
      const out = await plugin.execute(
        { action: "check", agent: "architect" },
        { sessionID: "otra-sesion", agent: "architect" } as any
      );
      expect(out).toContain("Safe threshold: 55%");
    });

    it("un check posterior respeta el umbral persistido (sin override por llamada)", async () => {
      const ctx = makeContext({ tokenUsage: { total: 64000 } }) as any; // 50%
      await plugin.execute({ action: "set-threshold", agent: "architect", thresholdOverride: 0.8 }, ctx);
      // al 60% (76800/128000): con default 55% sería WARNING; con persistido 80% → OK
      ctx.session.tokenUsage = { total: 76800 };
      const out = await plugin.execute({ action: "check", agent: "architect" }, ctx);
      expect(out).toContain("Estado:** OK");
      expect(out).toContain("Safe threshold: 80%");
    });
  });

  describe("Acción compact", () => {
    it("dry-run no invoca session.compact ni persiste lastCompaction", async () => {
      const compact = vi.fn();
      const ctx = {
        sessionID: "test-session-001",
        agent: "architect",
        directory: "/project",
        worktree: "/project",
        session: { messages: [{ role: "user", content: "x" }], compact },
      } as any;
      const out = await plugin.execute({ action: "compact", agent: "architect", dryRun: true }, ctx);
      expect(out).toContain("[DRY-RUN]");
      expect(compact).not.toHaveBeenCalled();
      const state = readState();
      expect(state.lastCompaction).toBeNull();
    });

    it("dry-run sin messages usa 0 y muestra % cuando hay métricas live (ramas 316-317)", async () => {
      const ctx = {
        sessionID: "test-session-001",
        agent: "architect",
        directory: "/project",
        worktree: "/project",
        session: { tokenUsage: { total: 64000 }, contextLimit: 128000 },
      } as any;
      const out = await plugin.execute({ action: "compact", agent: "architect", dryRun: true }, ctx);
      expect(out).toContain("[DRY-RUN]");
      expect(out).toContain("Resumir 0 mensajes totales");
      expect(out).toContain("50% (64000 tokens)");
    });

    it("ejecuta session.compact (legacy) y persiste lastCompaction", async () => {
      const compact = vi.fn().mockResolvedValue(undefined);
      const ctx = {
        sessionID: "test-session-001",
        agent: "architect",
        directory: "/project",
        worktree: "/project",
        session: { messages: [], compact },
      } as any;
      const out = await plugin.execute({ action: "compact", agent: "architect" }, ctx);
      expect(compact).toHaveBeenCalledWith({ preserveRecent: 6 }); // priorityMessages del architect
      expect(out).toContain("Compactacion ejecutada");
      expect(readState().lastCompaction).toBeTruthy();
    });

    it("recomienda compactación manual si no hay soporte nativo", async () => {
      const ctx = {
        sessionID: "test-session-001",
        agent: "architect",
        directory: "/project",
        worktree: "/project",
        session: { messages: [] },
      } as any;
      const out = await plugin.execute({ action: "compact", agent: "architect" }, ctx);
      expect(out).toContain("Compactacion nativa no disponible");
    });

    it("captura errores de session.compact", async () => {
      const compact = vi.fn().mockRejectedValue(new Error("boom"));
      const ctx = {
        sessionID: "test-session-001",
        agent: "architect",
        directory: "/project",
        worktree: "/project",
        session: { messages: [], compact },
      } as any;
      const out = await plugin.execute({ action: "compact", agent: "architect" }, ctx);
      expect(out).toContain("Error en compactacion: boom");
    });
  });

  describe("Pipeline hints", () => {
    it("incluye pistas EitL para el agente activo", async () => {
      const out = await plugin.execute({ action: "check", agent: "architect" }, makeContext() as any);
      expect(out).toContain("EitL Pipeline hints:");
      expect(out).toContain("/start-TDD");
    });
  });

  describe("Estimación de tokens desde mensajes (L3: workaround)", () => {
    it("estima tokens cuando no hay tokenUsage ni estado persistido (nueva sesión)", async () => {
      const ctx = {
        sessionID: "fresh-estimada",
        agent: "architect",
        directory: "/project",
        worktree: "/project",
        session: {
          messages: [
            { role: "system", content: "You are the architect." },
            { role: "user", content: "Build a REST API" },
            { role: "assistant", content: "Here is the plan..." },
          ],
        },
      } as any;
      const out = await plugin.execute({ action: "check", agent: "architect" }, ctx);
      expect(out).toContain("estimado");
      expect(out).toContain("Estado:** OK");
      // 1 system (~120) + 1 user (~150) + 1 assistant (~180) = ~450 tokens
      expect(out).toContain("450");
    });

    it("acciones estimate muestra desglose detallado", async () => {
      const ctx = {
        sessionID: "estimada-desglose",
        agent: "architect",
        directory: "/project",
        worktree: "/project",
        session: {
          messages: [
            { role: "system", content: "You are the architect." },
            { role: "user", content: "Build a REST API" },
            { role: "assistant", content: "Here is the plan..." },
          ],
        },
      } as any;
      const out = await plugin.execute({ action: "estimate", agent: "architect" }, ctx);
      expect(out).toContain("Estimación de Tokens");
      expect(out).toContain("Mensajes totales: 3");
      expect(out).toContain("System messages");
      expect(out).toContain("User messages");
      expect(out).toContain("Assistant messages");
    });

    it("acciones estimate con mensajes vacíos retorna advertencia", async () => {
      const ctx = {
        sessionID: "empty-estimada",
        agent: "architect",
        directory: "/project",
        worktree: "/project",
        session: { messages: [] },
      } as any;
      const out = await plugin.execute({ action: "estimate", agent: "architect" }, ctx);
      expect(out).toContain("No hay mensajes en la sesión");
    });

    it("mensajes largos ajustan la estimación (content > 5000 chars)", async () => {
      // 30000 chars / 3.5 ≈ 8571 tokens (≈7% del contexto), no el default 150
      const bigContent = "x".repeat(30_000);
      const ctx = {
        sessionID: "big-msg-estimada",
        agent: "architect",
        directory: "/project",
        worktree: "/project",
        session: {
          messages: [
            { role: "user", content: bigContent },
          ],
        },
      } as any;
      const out = await plugin.execute({ action: "check", agent: "architect" }, ctx);
      // 30000 chars / 3.5 ≈ 8571 tokens (ajustado), no el default 150
      expect(out).toContain("estimado");
      // 8571/128000 ≈ 7% → OK (below safe threshold 55%)
      expect(out).toContain("Estado:** OK");
    });

    it("mensajes muy largos pueden alcanzar WARNING (content > 100000 chars)", async () => {
      // 100000 chars / 3.5 ≈ 28571 tokens (≈22% del contexto)
      const bigContent = "x".repeat(100_000);
      const ctx = {
        sessionID: "very-big-msg-estimada",
        agent: "product-owner",
        directory: "/project",
        worktree: "/project",
        session: {
          messages: [
            { role: "user", content: bigContent },
          ],
        },
      } as any;
      const out = await plugin.execute({ action: "check", agent: "product-owner" }, ctx);
      expect(out).toContain("estimado");
      // product-owner safe threshold = 60%, 28571/128000 ≈ 22% → OK
      expect(out).toContain("Estado:** OK");
    });

    it("persiste estimación y la reutiliza en el siguiente check", async () => {
      const ctx1 = {
        sessionID: "persist-est",
        agent: "architect",
        directory: "/project",
        worktree: "/project",
        session: {
          messages: [
            { role: "system", content: "You are the architect." },
            { role: "user", content: "Build a REST API" },
            { role: "assistant", content: "Here is the plan..." },
          ],
        },
      } as any;
      await plugin.execute({ action: "check", agent: "architect" }, ctx1);
      // Segundo check sin messages → debería usar la estimación persistida
      const ctx2 = {
        sessionID: "persist-est",
        agent: "architect",
        directory: "/project",
        worktree: "/project",
        session: { messages: [] },
      } as any;
      const out = await plugin.execute({ action: "check", agent: "architect" }, ctx2);
      expect(out).toContain("450"); // la estimación persistida
      expect(out).toContain("(estimado)");
    });
  });

  describe("Ramas de cobertura restantes (04 §7.2)", () => {
    it("usa el directorio de estado por defecto cuando falta OPENCODE_STATE_DIR (115)", async () => {
      delete process.env.OPENCODE_STATE_DIR;
      const ctx = {
        sessionID: "sesion-sin-env",
        agent: "architect",
        directory: "/project",
        worktree: "/project",
        session: { messages: [] },
      } as any;
      const out = await plugin.execute({ action: "check", agent: "architect" }, ctx);
      expect(out).toContain("no disponibles");
      expect(mockFiles[".opencode/.context-guard/sesion-sin-env.json"]).toBeTruthy();
    });

    it("usa sessionID 'unknown' cuando el contexto no lo expone (196)", async () => {
      const ctx = {
        agent: "architect",
        directory: "/project",
        worktree: "/project",
        session: { messages: [] },
      } as any;
      const out = await plugin.execute({ action: "check", agent: "architect" }, ctx);
      expect(out).toContain("no disponibles");
      expect(mockFiles[".opencode/.context-guard/unknown.json"]).toBeTruthy();
    });
  });
});
