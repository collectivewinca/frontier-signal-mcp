import { publicBriefOnly } from "./brief";
import { BRIEFS, RAW_BASELINES } from "./embedded";

export const MENTION_COUNT_DISCLAIMER =
  "Mention counts are heuristics recorded on the public baseline, not search-engine hit counts. Do not invent additional counts.";

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const TOKEN_RE = /[a-z0-9]+/g;
const FUZZY_THRESHOLD = 0.72;

export class SignalError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SignalError";
  }
}

export type BrowserCheck = {
  status?: string | null;
  facts?: string[];
  notes?: string | null;
  observed?: string | null;
};

export type Source = {
  name: string;
  type: string;
  url: string;
  status: string;
  categories?: string;
  band?: string;
  referral?: string;
  notes?: string;
  checked?: string | null;
  browser?: BrowserCheck | null;
};

export type HotCategory = { category: string; mention_count: number };

export type Baseline = {
  observed: string;
  sources: Source[];
  hot: HotCategory[];
  deltas_vs_prev: string[];
  hot_note?: string | null;
  recheck?: string | null;
};

export type ProgrammeSummary = {
  name: string;
  url: string;
  band: string;
  referral: string;
  categories: string;
  status: string;
  notes: string;
  type: string;
  observed: string;
  checked: string | null;
};

export type ProgrammeDetail = ProgrammeSummary & {
  browser: BrowserCheck | null;
};

export type ProgrammeList = {
  observed: string;
  programme_count: number;
  programmes: ProgrammeSummary[];
  filters: { type: string | null; status: string | null; category: string | null };
};

export type ProgrammeLookup = {
  query: string;
  observed: string;
  match_kind: string;
  match: ProgrammeDetail | null;
  alternatives: string[];
  message?: string | null;
};

export type DemandMix = {
  observed: string;
  hot: HotCategory[];
  hot_note: string | null;
  disclaimer: string;
};

export type DeltasResult = {
  observed: string;
  deltas_vs_prev: string[];
  recheck: string | null;
};

export type BriefResult = {
  observed: string;
  markdown: string;
  public_only: boolean;
  path: string | null;
  message?: string | null;
};

export type ObservedDates = {
  dates: string[];
  latest: string | null;
  brief_dates: string[];
  latest_brief: string | null;
};

function tokens(text: string): string[] {
  return text.toLowerCase().match(TOKEN_RE) ?? [];
}

function lcsLength(a: string, b: string): number {
  const m = a.length;
  const n = b.length;
  const prev = new Array<number>(n + 1).fill(0);
  const cur = new Array<number>(n + 1).fill(0);
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      cur[j] = a[i - 1] === b[j - 1] ? prev[j - 1] + 1 : Math.max(prev[j], cur[j - 1]);
    }
    for (let j = 0; j <= n; j++) prev[j] = cur[j];
  }
  return prev[n];
}

function sequenceRatio(a: string, b: string): number {
  if (!a && !b) return 1;
  if (!a || !b) return 0;
  return (2 * lcsLength(a, b)) / (a.length + b.length);
}

function scoreName(query: string, name: string): [number, string] {
  const q = query.toLowerCase().trim();
  const n = name.toLowerCase().trim();
  if (!q || !n) return [0, "none"];
  if (q === n) return [1, "exact"];
  if (n.includes(q) || q.includes(n)) return [0.92, "substring"];
  const qTokens = tokens(q);
  const nTokens = tokens(n);
  if (qTokens.length && qTokens.every((token) => nTokens.includes(token))) {
    return [0.88, "substring"];
  }
  let ratio = sequenceRatio(q, n);
  for (const token of nTokens) {
    ratio = Math.max(ratio, sequenceRatio(q, token));
  }
  if (ratio >= FUZZY_THRESHOLD) return [ratio, "fuzzy"];
  return [ratio, "none"];
}

function coerceHot(value: unknown): HotCategory[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => {
    if (item && typeof item === "object" && !Array.isArray(item)) {
      const rec = item as { category?: unknown; mention_count?: unknown };
      return {
        category: String(rec.category ?? ""),
        mention_count: Number(rec.mention_count),
      };
    }
    if (Array.isArray(item) && item.length >= 2) {
      return { category: String(item[0]), mention_count: Number(item[1]) };
    }
    throw new SignalError(
      "hot entries must be [category, mention_count] pairs; refusing to invent a count",
    );
  });
}

function parseBaseline(raw: unknown): Baseline {
  if (!raw || typeof raw !== "object") {
    throw new SignalError("Invalid baseline JSON");
  }
  const rec = raw as Record<string, unknown>;
  const observed = String(rec.observed ?? "");
  if (!DATE_RE.test(observed)) {
    throw new SignalError(`observed must be YYYY-MM-DD, got ${JSON.stringify(rec.observed)}`);
  }
  const sources = Array.isArray(rec.sources) ? (rec.sources as Source[]) : [];
  return {
    observed,
    sources,
    hot: coerceHot(rec.hot),
    deltas_vs_prev: Array.isArray(rec.deltas_vs_prev)
      ? rec.deltas_vs_prev.map(String)
      : [],
    hot_note: rec.hot_note == null ? null : String(rec.hot_note),
    recheck: rec.recheck == null ? null : String(rec.recheck),
  };
}

function summary(source: Source, observed: string): ProgrammeSummary {
  return {
    name: source.name,
    url: source.url,
    band: source.band ?? "",
    referral: source.referral ?? "",
    categories: source.categories ?? "",
    status: source.status,
    notes: source.notes ?? "",
    type: source.type,
    observed,
    checked: source.checked ?? null,
  };
}

export class SignalStore {
  private baselines: Map<string, Baseline>;
  private briefs: Map<string, string>;

  constructor(rawBaselines: unknown[] = RAW_BASELINES, briefs: Record<string, string> = BRIEFS) {
    this.baselines = new Map();
    for (const raw of rawBaselines) {
      const baseline = parseBaseline(raw);
      this.baselines.set(baseline.observed, baseline);
    }
    this.briefs = new Map();
    for (const [date, markdown] of Object.entries(briefs)) {
      if (!DATE_RE.test(date)) continue;
      this.briefs.set(date, publicBriefOnly(markdown));
    }
  }

  dates(): string[] {
    return [...this.baselines.keys()].sort().reverse();
  }

  briefDates(): string[] {
    return [...this.briefs.keys()].sort().reverse();
  }

  latestDate(): string {
    const dates = this.dates();
    if (!dates.length) {
      throw new SignalError(
        "No baselines found. Drop a JSON cut in data/baselines/YYYY-MM-DD.json.",
      );
    }
    return dates[0];
  }

  getBaseline(observed?: string | null): Baseline {
    const date = (observed ?? "").trim() || this.latestDate();
    if (!DATE_RE.test(date)) {
      throw new SignalError(
        `observed must be YYYY-MM-DD, got ${JSON.stringify(observed)}. Available: ${this.dates().join(", ") || "(none)"}`,
      );
    }
    const baseline = this.baselines.get(date);
    if (!baseline) {
      throw new SignalError(
        `No baseline for ${date}. Available dates: ${this.dates().join(", ") || "(none)"}`,
      );
    }
    return baseline;
  }

  listObservedDates(): ObservedDates {
    const dates = this.dates();
    const briefs = this.briefDates();
    return {
      dates,
      latest: dates[0] ?? null,
      brief_dates: briefs,
      latest_brief: briefs[0] ?? null,
    };
  }

  listProgrammes(filters: {
    type?: string | null;
    status?: string | null;
    category?: string | null;
    observed?: string | null;
  } = {}): ProgrammeList {
    const baseline = this.getBaseline(filters.observed);
    const typeFilter = (filters.type ?? "").trim().toLowerCase() || null;
    const statusFilter = (filters.status ?? "").trim().toLowerCase() || null;
    const categoryFilter = (filters.category ?? "").trim().toLowerCase() || null;
    const programmes: ProgrammeSummary[] = [];
    for (const source of baseline.sources) {
      if (typeFilter && source.type.toLowerCase() !== typeFilter) continue;
      if (statusFilter && source.status.toLowerCase() !== statusFilter) continue;
      if (
        categoryFilter &&
        !(source.categories ?? "").toLowerCase().includes(categoryFilter)
      ) {
        continue;
      }
      programmes.push(summary(source, baseline.observed));
    }
    return {
      observed: baseline.observed,
      programme_count: programmes.length,
      programmes,
      filters: {
        type: (filters.type ?? "").trim() || null,
        status: (filters.status ?? "").trim() || null,
        category: (filters.category ?? "").trim() || null,
      },
    };
  }

  getProgramme(name: string, observed?: string | null): ProgrammeLookup {
    const query = (name ?? "").trim();
    const baseline = this.getBaseline(observed);
    if (!query) {
      return {
        query,
        observed: baseline.observed,
        match_kind: "none",
        match: null,
        alternatives: [],
        message: "Pass a programme name to look up. Nothing was invented.",
      };
    }
    const ranked: { score: number; kind: string; source: Source }[] = [];
    for (const source of baseline.sources) {
      const [score, kind] = scoreName(query, source.name);
      if (kind === "none") continue;
      ranked.push({ score, kind, source });
    }
    if (!ranked.length) {
      return {
        query,
        observed: baseline.observed,
        match_kind: "none",
        match: null,
        alternatives: [],
        message: `No programme matching ${JSON.stringify(query)} on ${baseline.observed}. Names are taken from the baseline; this tool does not invent programmes.`,
      };
    }
    ranked.sort(
      (a, b) => b.score - a.score || a.source.name.localeCompare(b.source.name),
    );
    const best = ranked[0];
    const alternatives = ranked
      .slice(1)
      .filter(
        (row) =>
          row.score >= Math.min(best.score, FUZZY_THRESHOLD) ||
          row.kind === "exact" ||
          row.kind === "substring",
      )
      .map((row) => row.source.name);
    return {
      query,
      observed: baseline.observed,
      match_kind: best.kind,
      match: {
        ...summary(best.source, baseline.observed),
        browser: best.source.browser ?? null,
      },
      alternatives,
    };
  }

  demandMix(observed?: string | null): DemandMix {
    const baseline = this.getBaseline(observed);
    return {
      observed: baseline.observed,
      hot: [...baseline.hot],
      hot_note: baseline.hot_note ?? null,
      disclaimer: MENTION_COUNT_DISCLAIMER,
    };
  }

  deltas(observed?: string | null): DeltasResult {
    const baseline = this.getBaseline(observed);
    return {
      observed: baseline.observed,
      deltas_vs_prev: [...baseline.deltas_vs_prev],
      recheck: baseline.recheck ?? null,
    };
  }

  latestBrief(observed?: string | null): BriefResult {
    let date: string;
    if (observed && observed.trim()) {
      date = observed.trim();
      if (!DATE_RE.test(date)) {
        throw new SignalError(
          `observed must be YYYY-MM-DD, got ${JSON.stringify(observed)}. Available briefs: ${this.briefDates().join(", ") || "(none)"}`,
        );
      }
    } else {
      const briefs = this.briefDates();
      if (!briefs.length) {
        throw new SignalError(
          "No public briefs found. Drop markdown in data/briefs/YYYY-MM-DD.md (public cut only).",
        );
      }
      date = briefs[0];
    }
    const markdown = this.briefs.get(date);
    if (markdown == null) {
      throw new SignalError(
        `No public brief for ${date}. Available briefs: ${this.briefDates().join(", ") || "(none)"}`,
      );
    }
    if (!markdown.trim()) {
      throw new SignalError(
        `Brief ${date} was empty after stripping gated watchlist content. This server never serves gated copy.`,
      );
    }
    return {
      observed: date,
      markdown,
      public_only: true,
      path: `data/briefs/${date}.md`,
    };
  }
}

let store: SignalStore | undefined;

export function getStore(): SignalStore {
  store ??= new SignalStore();
  return store;
}
