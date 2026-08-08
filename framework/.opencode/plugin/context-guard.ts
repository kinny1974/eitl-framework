import { tool } from "@opencode-ai/plugin";
import * as fs from "fs";
import * as path from "path";

// Context Guard Plugin — EitL Pipeline Edition
// Vigila la ventana de contexto para 5 agentes:
// scrum-master, product-owner, architect, tdd-engineer, validator

interface AgentProfile {
  name: string;
  role: string;
  safeThreshold: number;
  criticalThreshold: number;
  priorityMessages: number;
}

const AGENTS: Record<string, AgentProfile> = {
  "scrum-master": {
    name: "scrum-master",
    role: "Facilitates Agile ceremonies and resolves blockers",
    safeThreshold: 0.65,
    criticalThreshold: 0.80,
    priorityMessages: 8,
  },
  "product-owner": {
    name: "product-owner",
    role: "Defines user stories and acceptance criteria",
    safeThreshold: 0.60,
    criticalThreshold: 0.75,
    priorityMessages: 10,
  },
  "architect": {
    name: "architect",
    role: "Designs architecture and makes technical decisions",
    safeThreshold: 0.55,
    criticalThreshold: 0.70,
    priorityMessages: 6,
  },
  "tdd-engineer": {
    name: "tdd-engineer",
    role: "Implements with TDD and continuous refactoring",
    safeThreshold: 0.60,
    criticalThreshold: 0.78,
    priorityMessages: 8,
  },
  "validator": {
    name: "validator",
    role: "Validates quality, tests, and acceptance criteria",
    safeThreshold: 0.65,
    criticalThreshold: 0.80,
    priorityMessages: 10,
  },
};

function getStatePath(sessionId: string): string {
  const base = process.env.OPENCODE_STATE_DIR || ".opencode/.context-guard";
  return path.join(base, `${sessionId}.json`);
}

function loadState(sessionId: string): any {
  try {
    const p = getStatePath(sessionId);
    if (fs.existsSync(p)) {
      return JSON.parse(fs.readFileSync(p, "utf-8"));
    }
  } catch {}
  return { alertsSent: [], lastCompaction: null, agentSwitches: [] };
}

function saveState(sessionId: string, state: any) {
  const p = getStatePath(sessionId);
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, JSON.stringify(state, null, 2));
}

function estimateTokens(text: string): number {
  return Math.ceil(text.length / 3.5);
}

export default tool({
  name: "context-guard",
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
      .describe("Which agent profile to use. 'auto' detects from session metadata."),

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
    const session = context.session;
    const sessionId = context.sessionID || "unknown";

    let activeAgent = agentArg;
    if (activeAgent === "auto") {
      const sysMsgs = session.messages?.filter((m: any) => m.role === "system") || [];
      const lastSys = sysMsgs[sysMsgs.length - 1]?.content || "";
      for (const key of Object.keys(AGENTS)) {
        if (lastSys.toLowerCase().includes(key)) {
          activeAgent = key;
          break;
        }
      }
      if (activeAgent === "auto") activeAgent = "architect";
    }

    const profile = AGENTS[activeAgent];
    const safeThreshold = thresholdOverride ?? profile.safeThreshold;
    const criticalThreshold = profile.criticalThreshold;
    const state = loadState(sessionId);

    const usage = (session as any).tokenUsage || { total: 0, prompt: 0, completion: 0 };
    const limit = (session as any).contextLimit || (session as any).model?.info?.limit?.context || 128000;

    let totalTokens = usage.total || 0;
    if (totalTokens === 0 && session.messages) {
      const allText = session.messages.map((m: any) =>
        typeof m.content === "string" ? m.content : JSON.stringify(m.content)
      ).join("\n");
      totalTokens = estimateTokens(allText);
    }

    const ratio = totalTokens / limit;
    const percent = Math.round(ratio * 100);
    const remaining = limit - totalTokens;

    if (action === "report") {
      return formatReport(activeAgent, profile, percent, remaining, limit, totalTokens, state);
    }

    if (action === "set-threshold") {
      if (!thresholdOverride) return "Error: thresholdOverride requerido para set-threshold";
      profile.safeThreshold = thresholdOverride;
      return `✅ Threshold for ${activeAgent} adjusted to ${Math.round(thresholdOverride * 100)}%`;
    }

    if (action === "switch-agent") {
      state.agentSwitches.push({
        from: state.lastAgent || "unknown",
        to: activeAgent,
        at: new Date().toISOString(),
        tokensAtSwitch: totalTokens,
      });
      state.lastAgent = activeAgent;
      saveState(sessionId, state);
      return `🔄 Switch to agent **${activeAgent}** registered. Current context: ${percent}% (${totalTokens}/${limit} tokens).`;
    }

    let alertLevel: "ok" | "warning" | "critical" = "ok";
    let recommendation = "";

    if (ratio >= criticalThreshold) {
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

    state.alertsSent.push({
      level: alertLevel,
      percent,
      tokens: totalTokens,
      agent: activeAgent,
      at: new Date().toISOString(),
    });
    saveState(sessionId, state);

    if (action === "compact") {
      if (dryRun) {
        return (
          `🧪 [DRY-RUN] Compactacion simulada para **${activeAgent}**\n` +
          `   - Preservar ultimos ${preserveRecent ?? profile.priorityMessages} mensajes\n` +
          `   - Resumir ${session.messages?.length || 0} mensajes totales\n` +
          `   - Estado actual: ${percent}% (${totalTokens} tokens)`
        );
      }

      try {
        if (typeof (session as any).compact === "function") {
          await (session as any).compact({
            preserveRecent: preserveRecent ?? profile.priorityMessages,
          });
          state.lastCompaction = new Date().toISOString();
          saveState(sessionId, state);
          return `🗜️ Compactacion ejecutada para **${activeAgent}**. Estado previo: ${percent}% (${totalTokens} tokens).`;
        } else {
          return (
            `⚠️ Compactacion nativa no disponible en esta version de OpenCode.\n` +
            `   Recomendacion manual: reinicia la sesion o usa /compact en el TUI.\n` +
            `   ${recommendation}`
          );
        }
      } catch (e: any) {
        return `❌ Error en compactacion: ${e.message}`;
      }
    }

    const header = `📊 **Context Guard** | Agente: \`${activeAgent}\` | Profile: ${profile.role}`;
    const body = [
      `• Tokens useds: **${totalTokens.toLocaleString()}** / ${limit.toLocaleString()}`,
      `• Porcentaje: **${percent}%**`,
      `• Remaining: **${remaining.toLocaleString()}** tokens`,
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
  state: any
): string {
  const alerts = state.alertsSent.slice(-10);
  const switches = state.agentSwitches.slice(-10);

  return (
    `📈 **Context Guard Report** — ${agent}\n` +
    `======================================\n` +
    `Profile: ${profile.role}\n` +
    `Tokens: ${totalTokens.toLocaleString()} / ${limit.toLocaleString()} (${percent}%)\n` +
    `Remaining: ${remaining.toLocaleString()}\n` +
    `Last compaction: ${state.lastCompaction || "N/A"}\n\n` +
    `Last 10 alerts:\n` +
    (alerts.length
      ? alerts
          .map(
            (a: any) =>
              `  [${a.at}] ${a.level.toUpperCase()} — ${a.percent}% (${a.tokens} tokens)`
          )
          .join("\n")
      : "  (none)") +
    `\n\nLast 10 agent switches:\n` +
    (switches.length
      ? switches
          .map(
            (s: any) =>
              `  [${s.at}] ${s.from} → ${s.to} @ ${s.tokensAtSwitch} tokens`
          )
          .join("\n")
      : "  (ninguno)")
  );
}
