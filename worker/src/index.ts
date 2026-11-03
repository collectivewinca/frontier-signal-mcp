import { createMcpHandler } from "agents/mcp/server";
import { McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";

import { landingPage, privacyHtml, privacyMarkdown } from "./pages";
import { SignalError, getStore } from "./store";

const VERSION = "0.2.0";

const INSTRUCTIONS = `You are querying VE Lab Frontier Signal: verified AI data-broker buyer programmes and demand signals.

Rules:
- Use only values returned by these tools. Never invent hit counts, URLs, programmes, prices, or job counts.
- Mention counts in demand_mix are heuristics recorded on the baseline, not search-engine hit counts.
- This server is public and read-only. It does not expose gated watchlist content.
- If a date is missing, report the available dates from list_observed_dates.`;

const READ_ONLY = {
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false,
} as const;

const observedField = z
  .string()
  .optional()
  .describe("Baseline date YYYY-MM-DD. Omit for the latest committed cut.");

function ok(data: unknown) {
  return {
    structuredContent: data as Record<string, unknown>,
    content: [{ type: "text" as const, text: JSON.stringify(data, null, 2) }],
  };
}

function fail(error: unknown) {
  const message = error instanceof Error ? error.message : String(error);
  return {
    isError: true as const,
    content: [{ type: "text" as const, text: message }],
  };
}

function runTool<T>(fn: () => T) {
  try {
    return ok(fn());
  } catch (error) {
    if (error instanceof SignalError) return fail(error);
    throw error;
  }
}

function createServer() {
  const server = new McpServer({
    name: "Frontier Signal",
    version: VERSION,
    title: "Frontier Signal",
    description: INSTRUCTIONS,
    websiteUrl: "https://velab.org/frontier-signal/",
  });

  server.registerTool(
    "list_buyer_programmes",
    {
      title: "List buyer programmes",
      description:
        "List verified buyer programmes (and other sources) from a public baseline. Returns name, url, band, referral, categories, status, notes, and type. An empty list means no rows matched — programmes are never invented.",
      annotations: { title: "List buyer programmes", ...READ_ONLY },
      inputSchema: {
        type: z
          .string()
          .optional()
          .describe("Filter by source type: buyer, lab, or seed. Omit for all."),
        status: z
          .string()
          .optional()
          .describe(
            "Filter by exact status (case-insensitive), e.g. ok, browser-ok, dead, board-only, 200.",
          ),
        category: z
          .string()
          .optional()
          .describe("Substring match against the categories field (case-insensitive)."),
        observed: observedField,
      },
    },
    async ({ type, status, category, observed }) =>
      runTool(() =>
        getStore().listProgrammes({ type, status, category, observed }),
      ),
  );

  server.registerTool(
    "get_programme",
    {
      title: "Get a programme",
      description:
        "Look up one verified programme by exact or fuzzy name. A miss returns match_kind=none — this tool does not invent a programme.",
      annotations: { title: "Get a programme", ...READ_ONLY },
      inputSchema: {
        name: z
          .string()
          .describe("Programme name to look up (exact, substring, or fuzzy)."),
        observed: observedField,
      },
    },
    async ({ name, observed }) =>
      runTool(() => getStore().getProgramme(name, observed)),
  );

  server.registerTool(
    "demand_mix",
    {
      title: "Demand mix",
      description:
        "Return hot demand categories recorded on a public baseline. mention_count values are heuristics copied from the JSON cut, not hit counts. This tool never invents additional categories or counts.",
      annotations: { title: "Demand mix", ...READ_ONLY },
      inputSchema: { observed: observedField },
    },
    async ({ observed }) => runTool(() => getStore().demandMix(observed)),
  );

  server.registerTool(
    "latest_brief",
    {
      title: "Latest public brief",
      description:
        "Return the public Frontier Signal brief markdown for a date. Gated watchlist sections are stripped if present. A brief is never synthesised.",
      annotations: { title: "Latest public brief", ...READ_ONLY },
      inputSchema: {
        observed: z
          .string()
          .optional()
          .describe("Brief date YYYY-MM-DD. Omit for the latest public brief."),
      },
    },
    async ({ observed }) => runTool(() => getStore().latestBrief(observed)),
  );

  server.registerTool(
    "deltas",
    {
      title: "Baseline deltas",
      description:
        "Return deltas_vs_prev (and recheck notes, if any) for a baseline cut. These are the change notes recorded on that JSON file. This tool does not compute new diffs.",
      annotations: { title: "Baseline deltas", ...READ_ONLY },
      inputSchema: { observed: observedField },
    },
    async ({ observed }) => runTool(() => getStore().deltas(observed)),
  );

  server.registerTool(
    "list_observed_dates",
    {
      title: "List observed dates",
      description:
        "List baseline dates (and public brief dates) available in this checkout. No live fetch is performed.",
      annotations: { title: "List observed dates", ...READ_ONLY },
      inputSchema: {},
    },
    async () => runTool(() => getStore().listObservedDates()),
  );

  return server;
}

const mcpHandler = createMcpHandler(createServer, {
  route: "/mcp",
  allowedOriginHostnames: "*",
  corsOptions: { origin: "*", methods: "GET, POST, DELETE, OPTIONS" },
});

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";
    if (path === "/") return landingPage(request);
    if (path === "/privacy") return privacyHtml();
    if (path === "/privacy.md") return privacyMarkdown();
    if (path === "/health") {
      return Response.json({
        ok: true,
        name: "Frontier Signal",
        version: VERSION,
        mcp: "/mcp",
        privacy: "/privacy",
      });
    }
    return mcpHandler(request, env, ctx);
  },
} satisfies ExportedHandler<Env>;
