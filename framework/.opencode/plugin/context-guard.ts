import { tool, type Plugin, type ToolContext } from "@opencode-ai/plugin";
import * as fs from "fs";
import * as path from "path";

// Context Guard Plugin — EitL Pipeline Edition
// Migrado a la API actual de @opencode-ai/plugin:
//  - El nombre del tool se define como clave del mapa `tool` en los hooks del plugin.
//  - ToolContext ya no expone `session`; la detección de agente usa `context.agent`
//    y el acceso a métricas de sesión es defensivo (fuente legacy opcional).
//  - El tipado de `activeAgent` es estricto (keyof AGENTS).

interface AgentProfile {
  name: string;
  role: string;
  safeThreshold: number;
  criticalThreshold: number;
  priorityMessages: number;
}

type AgentKey = "scrum-master" | "product-owner" | "architect" | "tdd-engineer" | "validator";

const AGENTS: Record<AgentKey, AgentProfile> = {
  "scrum-master": {
    name: "scrum-master",
    role: "Facilitates Agile ceremonies and resolves blockers",
    safeThreshold: 0.65,
    criticalThreshold: 0.8,
    priorityMessages: 8,
  },
  "product-owner": {
    name: "product-owner",
    role: "Defines user stories and acceptance criteria",
    safeThreshold: 0.6,
    criticalThreshold: 0.75,
    priorityMessages: 10,
  },
  architect: {
    name: "architect",
    role: "Designs architecture and makes technical decisions",
    safeThreshold: 0.55,
    criticalThreshold: 0.7,
    priorityMessages: 6,
  },
  "tdd-engineer": {
    name: "tdd-engineer",
    role: "Implements with TDD and continuous refactoring",
    safeThreshold: 0.6,
    criticalThreshold: 0.78,
    priorityMessages: 8,
  },
  validator: {
    name: "validator",
    role: "Validates quality, tests, and acceptance criteria",
    safeThreshold: 0.65,
    criticalThreshold: 0.8,
    priorityMessages: 10,
  },
};

const AGENT_KEYS = Object.keys(AGENTS) as AgentKey[];

function isAgentKey(value: string): value is AgentKey {
  return AGENT_KEYS.includes(value as AgentKey);
}

const DEFAULT_LIMIT = 128000;

// Formateo determinista (B3): fija explícitamente el locale en-US para que la salida
// sea idéntica en cualquier máquina/idioma del SO (toLocaleString() dependía del
// locale del sistema: 64.000 vs 64,000).
const fmtTokens = new Intl.NumberFormat("en-US");
const formatTokens = (n: number) => fmtTokens.format(n);

// Forma opcional de "sesión" que algunos runtimes/versiones pueden inyectar en el
// contexto. La API actual de ToolContext NO la garantiza; todo acceso es defensivo.
interface SessionLike {
  tokenUsage?: { total?: number; prompt?: number; completion?: number };
  contextLimit?: number;
  model?: { info?: { limit?: { context?: number } } };
  messages?: Array<{ role?: string; content?: unknown }>;
  compact?: (opts?: unknown) => Promise<unknown>;
}

function getSessionLike(context: ToolContext): SessionLike | undefined {
  return (context as unknown as { session?: SessionLike }).session;
}

type UsageSource = "live" | "state" | "none";

interface GuardState {
  alertsSent: Array<{
    level: "ok" | "warning" | "critical";
    percent: number;
    tokens: number;
    agent: string;
    at: string;
  }>;
  lastCompaction: string | null;
  agentSwitches: Array<{
    from: string;
    to: string;
    at: string;
    tokensAtSwitch: number;
  }>;
  lastAgent?: string;
  lastTokenUsage?: { total: number; at: string };
  lastTokenLimit?: number;
  // L2: umbrales seguros persistentes por agente (acción set-threshold).
  // Sin esto, el ajuste mutaba el perfil compartido AGENTS solo en memoria
  // (perdido al reiniciar y compartido entre sesiones).
  thresholdOverrides?: Partial<Record<AgentKey, number>>;
}

function getStatePath(sessionId: string): string {
  const base = process.env.OPENCODE_STATE_DIR || ".opencode/.context-guard";
  return path.join(base, `${sessionId}.json`);
}

// E/S asíncrona (fs.promises) para no bloquear el event loop en la ruta caliente
// (cuello de botella B2). loadState/saveState son async y se await-ean en execute.
// Nota (race de concurrencia): con E/S async, dos execute() concurrentes de la misma
// sesión pueden leer-modificar-escribir el mismo estado y el último escritor gana
// (se pierde la alerta/switch del otro). En el uso típico —una invocación por turno
// de agente— la probabilidad es baja; si llegara a ser un problema, serializar por
// sessionId con una cola o volver a escritura síncrona.
async function loadState(sessionId: string): Promise<GuardState> {
  try {
    const p = getStatePath(sessionId);
    const raw = await fs.promises.readFile(p, "utf-8");
    return JSON.parse(raw) as GuardState;
  } catch {
    // JSON corrupto o archivo inexistente: estado por defecto (sin romper el guard)
  }
  return { alertsSent: [], lastCompaction: null, agentSwitches: [] };
}

// Historiales acotados: cada check/switch agrega una entrada, así que sin poda el
// archivo de estado crece sin límite y cada escritura re-serializa todo el
// historial (acumulado O(n²)). Al podar a las MAX_HISTORY más recientes, la
// serialización queda acotada y el costo amortizado por escritura es O(1).
// El reporte solo muestra las últimas 10 alertas/switches, así que 50 sobra.
const MAX_HISTORY = 50;

function pruneHistory<T>(arr: T[], max: number = MAX_HISTORY): T[] {
  return arr.length > max ? arr.slice(arr.length - max) : arr;
}

async function saveState(sessionId: string, state: GuardState) {
  state.alertsSent = pruneHistory(state.alertsSent);
  state.agentSwitches = pruneHistory(state.agentSwitches);
  const p = getStatePath(sessionId);
  await fs.promises.mkdir(path.dirname(p), { recursive: true });
  await fs.promises.writeFile(p, JSON.stringify(state, null, 2));
}

const contextGuardTool = tool({
  description:
    "Monitors context window usage for EitL pipeline agents. " +
    "Returns token stats, alerts, and compaction recommendations. " +
    "Invoke before /start-SDD, /start-TDD, /start-IMPL, /regen, or /status.",

  args: {
    action: tool.schema
      .enum(["check", "compact", "switch-agent", "report", "set-threshold"])
      .default("check")
      .describe("What the guard should do"),

    agent: tool.schema
      .enum(["scrum-master", "product-owner", "architect", "tdd-engineer", "validator", "auto"])
      .default("auto")
      .describe("Which agent profile to use. 'auto' uses the current session agent."),

    thresholdOverride: tool.schema
      .number()
      .min(0.1)
      .max(0.95)
      .optional()
      .describe("Override the safe threshold for this check (0.1-0.95)."),

    preserveRecent: tool.schema
      .number()
      .int()
      .min(1)
      .max(50)
      .optional()
      .describe("How many recent messages to preserve during compaction."),

    dryRun: tool.schema
      .boolean()
      .default(false)
      .describe("If true, only simulate compaction without mutating session."),
  },

  async execute(args, context) {
    const { action, agent: agentArg, thresholdOverride, preserveRecent, dryRun } = args;
    const sessionId = context.sessionID || "unknown";

    // 1) Resolución del agente (tipado estricto):
    //    - agente explícito → se usa tal cual (el enum excluye "auto" en este ramo)
    //    - "auto" → usa el agente de la sesión actual (`context.agent`)
    //    - fallback → "architect"
    let activeAgent: AgentKey;
    if (agentArg === "auto") {
      activeAgent = isAgentKey(context.agent) ? context.agent : "architect";
    } else {
      activeAgent = agentArg;
    }

    const profile = AGENTS[activeAgent];
    const criticalThreshold = profile.criticalThreshold;
    const state = await loadState(sessionId);
    // L2: el umbral seguro se resuelve así:
    //   thresholdOverride (por llamada) > umbral persistido (set-threshold) > default del perfil
    const safeThreshold =
      thresholdOverride ?? state.thresholdOverrides?.[activeAgent] ?? profile.safeThreshold;

    // 2) Métricas de uso de tokens:
    //    live (fuente legacy opcional) → estado persistido → no disponibles
    const sessionLike = getSessionLike(context);
    const liveUsage = sessionLike?.tokenUsage;
    const liveLimit =
      sessionLike?.contextLimit ??
      sessionLike?.model?.info?.limit?.context ??
      (context as unknown as { contextLimit?: number }).contextLimit;

    // hasLive distingue "sin datos" de "0 tokens reportados" (live 0 es válido y
    // prevalece sobre las métricas persistidas, evitando datos obsoletos)
    const hasLive = typeof liveUsage?.total === "number";
    // hasLive garantiza que liveUsage.total es number; el ternario evita la rama
    // muerta del `?? 0` (que v8 contaba como no cubierta en la línea 229).
    let totalTokens = hasLive ? liveUsage!.total! : 0;
    let limit = typeof liveLimit === "number" ? liveLimit : 0;
    let usageSource: UsageSource = "none";

    if (hasLive) {
      usageSource = "live";
      if (!limit) limit = DEFAULT_LIMIT;
    } else if (state.lastTokenUsage && state.lastTokenUsage.total > 0) {
      totalTokens = state.lastTokenUsage.total;
      limit = state.lastTokenLimit || DEFAULT_LIMIT;
      usageSource = "state";
    } else {
      limit = liveLimit || DEFAULT_LIMIT;
    }

    const ratio = usageSource === "none" ? 0 : totalTokens / limit;
    const percent = Math.round(ratio * 100);
    const remaining = limit - totalTokens;

    if (action === "report") {
      return formatReport(activeAgent, profile, percent, remaining, limit, totalTokens, state);
    }

    if (action === "set-threshold") {
      if (!thresholdOverride) return "Error: thresholdOverride requerido para set-threshold";
      // L2: persistir en el estado de la sesión (antes mutaba el AGENTS global en memoria)
      state.thresholdOverrides = {
        ...(state.thresholdOverrides ?? {}),
        [activeAgent]: thresholdOverride,
      };
      await saveState(sessionId, state);
      return `✅ Threshold for ${activeAgent} adjusted to ${Math.round(thresholdOverride * 100)}% (persistido)`;
    }

    if (action === "switch-agent") {
      state.agentSwitches.push({
        from: state.lastAgent || "unknown",
        to: activeAgent,
        at: new Date().toISOString(),
        tokensAtSwitch: totalTokens,
      });
      state.lastAgent = activeAgent;
      await saveState(sessionId, state);
      return `🔄 Switch to agent **${activeAgent}** registered. Current context: ${percent}% (${totalTokens}/${limit} tokens).`;
    }

    let alertLevel: "ok" | "warning" | "critical" = "ok";
    let recommendation = "";

    if (usageSource === "none") {
      recommendation =
        "ℹ️ No hay métricas de uso de tokens disponibles: la API actual de " +
        "ToolContext no expone tokenUsage. Ejecuta el guard en una sesión que " +
        "reporte uso, o compacta manualmente con /compact en el TUI.";
    } else if (ratio >= criticalThreshold) {
      alertLevel = "critical";
      recommendation =
        `🚨 **CRITICAL**: Context at ${percent}%. Immediate compaction recommended.\n` +
        `   Ejecuta: /compact  o  context-guard({ action: "compact", agent: "${activeAgent}" })`;
    } else if (ratio >= safeThreshold) {
      alertLevel = "warning";
      recommendation =
        `⚠️ **WARNING**: Context at ${percent}%. Safe threshold (${Math.round(safeThreshold * 100)}%) exceeded.\n` +
        `   Consider: /compact before continuing con el pipeline.`;
    } else {
      recommendation = `✅ Healthy context: ${percent}% used (${totalTokens}/${limit} tokens).`;
    }

    // 3) Persistencia: historial de alertas + métricas para continuidad entre checks
    state.alertsSent.push({
      level: alertLevel,
      percent,
      tokens: totalTokens,
      agent: activeAgent,
      at: new Date().toISOString(),
    });
    if (usageSource === "live") {
      state.lastTokenUsage = { total: totalTokens, at: new Date().toISOString() };
      state.lastTokenLimit = limit;
    }
    await saveState(sessionId, state);

    if (action === "compact") {
      if (dryRun) {
        return (
          `🧪 [DRY-RUN] Compactacion simulada para **${activeAgent}**\n` +
          `   - Preservar ultimos ${preserveRecent ?? profile.priorityMessages} mensajes\n` +
          `   - Resumir ${sessionLike?.messages?.length ?? 0} mensajes totales\n` +
          `   - Estado actual: ${usageSource === "none" ? "sin métricas" : `${percent}% (${totalTokens} tokens)`}`
        );
      }

      // Compactación nativa: la API actual no garantiza `session.compact` en
      // ToolContext; se intenta de forma defensiva por si el runtime la inyecta.
      if (typeof sessionLike?.compact === "function") {
        try {
          await sessionLike.compact({ preserveRecent: preserveRecent ?? profile.priorityMessages });
          state.lastCompaction = new Date().toISOString();
          await saveState(sessionId, state);
          return `🗜️ Compactacion ejecutada para **${activeAgent}**. Estado previo: ${percent}% (${totalTokens} tokens).`;
        } catch (e: any) {
          return `❌ Error en compactacion: ${e.message}`;
        }
      }

      return (
        `⚠️ Compactacion nativa no disponible en esta version de OpenCode.\n` +
        `   Recomendacion manual: reinicia la sesion o usa /compact en el TUI.\n` +
        `   ${recommendation}`
      );
    }

    const tokensLine =
      usageSource === "none"
        ? "• Tokens: **no disponibles** (la API actual no expone tokenUsage)"
        : usageSource === "state"
          ? `• Tokens useds (persistido): **${formatTokens(totalTokens)}** / ${formatTokens(limit)}`
          : `• Tokens useds: **${formatTokens(totalTokens)}** / ${formatTokens(limit)}`;
    const percentLine =
      usageSource === "none" ? "• Porcentaje: **—**" : `• Porcentaje: **${percent}%**`;
    const remainingLine =
      usageSource === "none" ? "• Remaining: **—**" : `• Remaining: **${formatTokens(remaining)}** tokens`;

    const header = `📊 **Context Guard** | Agente: \`${activeAgent}\` | Profile: ${profile.role}`;
    const body = [
      tokensLine,
      percentLine,
      remainingLine,
      `• Safe threshold: ${Math.round(safeThreshold * 100)}%`,
      `• Umbral critico: ${Math.round(criticalThreshold * 100)}%`,
      ``,
      `**Estado:** ${alertLevel.toUpperCase()}`,
      ``,
      recommendation,
    ].join("\n");

    const pipelineHint =
      `\n\n💡 **EitL Pipeline hints:**\n` +
      `- Before /start-SDD: make sure you are under < ${Math.round(safeThreshold * 100)}%\n` +
      `- Before /start-TDD: ideal < 50% (the tdd-engineer agent consumes a lot of context with tests)\n` +
      `- Before /start-IMPL: if you are over > ${Math.round(criticalThreshold * 100)}%, compact first\n` +
      `- Use /regen only if there is enough space to regenerate without truncation`;

    return `${header}\n\n${body}${pipelineHint}`;
  },
});

function formatReport(
  agent: string,
  profile: AgentProfile,
  percent: number,
  remaining: number,
  limit: number,
  totalTokens: number,
  state: GuardState
): string {
  const alerts = state.alertsSent.slice(-10);
  const switches = state.agentSwitches.slice(-10);

  return (
    `📈 **Context Guard Report** — ${agent}\n` +
    `======================================\n` +
    `Profile: ${profile.role}\n` +
    `Tokens: ${formatTokens(totalTokens)} / ${formatTokens(limit)} (${percent}%)\n` +
    `Remaining: ${formatTokens(remaining)}\n` +
    `Last compaction: ${state.lastCompaction || "N/A"}\n\n` +
    `Last 10 alerts:\n` +
    (alerts.length
      ? alerts
          .map(
            (a) =>
              `  [${a.at}] ${a.level.toUpperCase()} — ${a.percent}% (${a.tokens} tokens)`
          )
          .join("\n")
      : "  (none)") +
    `\n\nLast 10 agent switches:\n` +
    (switches.length
      ? switches
          .map(
            (s) =>
              `  [${s.at}] ${s.from} → ${s.to} @ ${s.tokensAtSwitch} tokens`
          )
          .join("\n")
      : "  (ninguno)")
  );
}

/**
 * Punto de entrada del plugin para la API actual de @opencode-ai/plugin.
 * El nombre del tool se define como clave del mapa `tool` en los hooks.
 */
export const server: Plugin = async () => ({
  tool: {
    "context-guard": contextGuardTool,
  },
});

// Default export: el tool en sí, para que la suite de tests pueda importarlo
// directamente. En runtime, OpenCode carga el hook `server`.
export default contextGuardTool;
