import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { publicBriefOnly } from "../src/brief";
import { SignalError, SignalStore } from "../src/store";

const repoRoot = join(dirname(fileURLToPath(import.meta.url)), "../..");

function loadBaseline(date: string): unknown {
  return JSON.parse(
    readFileSync(join(repoRoot, "data/baselines", `${date}.json`), "utf8"),
  );
}

describe("SignalStore", () => {
  const store = new SignalStore();

  it("parses committed baselines without inventing hot counts", () => {
    const mix = store.demandMix("2026-11-03");
    const raw = loadBaseline("2026-11-03") as { hot: [string, number][] };
    expect(mix.hot.map((row) => [row.category, row.mention_count])).toEqual(raw.hot);
    expect(mix.disclaimer.toLowerCase()).toContain("hit count");
  });

  it("lists and filters programmes", () => {
    expect(store.listProgrammes({ observed: "2026-11-03" }).programme_count).toBe(24);
    const buyers = store.listProgrammes({ type: "buyer", observed: "2026-11-03" });
    expect(buyers.programme_count).toBe(17);
    const dead = store.listProgrammes({ status: "dead", observed: "2026-11-03" });
    expect(dead.programmes.map((row) => row.name).sort()).toEqual(["Grepped", "HUMXN"]);
  });

  it("looks up programmes by exact and fuzzy name", () => {
    const exact = store.getProgramme("Handshake AI", "2026-11-03");
    expect(exact.match_kind).toBe("exact");
    expect(exact.match?.url).toBe("https://joinhandshake.com/ai/");
    const fuzzy = store.getProgramme("lazarus");
    expect(["substring", "fuzzy"]).toContain(fuzzy.match_kind);
    expect(fuzzy.match?.name).toBe("Turing (Lazarus)");
    const missing = store.getProgramme("not-a-real-programme-zzz");
    expect(missing.match_kind).toBe("none");
    expect(missing.match).toBeNull();
  });

  it("returns latest deltas and observed dates", () => {
    const dates = store.listObservedDates();
    expect(dates.dates).toEqual(["2026-11-03", "2026-11-02", "2026-10-30"]);
    expect(dates.latest).toBe("2026-11-03");
    const deltas = store.deltas();
    expect(deltas.deltas_vs_prev.some((note) => note.includes("Lazarus"))).toBe(true);
  });

  it("serves the public brief only", () => {
    const brief = store.latestBrief();
    expect(brief.public_only).toBe(true);
    expect(brief.markdown).toContain("Public brief");
    expect(brief.markdown).not.toContain("Gated full answers");
    expect(brief.markdown).not.toContain("Implied capability");
  });

  it("errors on unknown dates instead of inventing a cut", () => {
    expect(() => store.getBaseline("1999-01-01")).toThrow(SignalError);
    expect(() => store.getBaseline("1999-01-01")).toThrow(/Available/);
  });
});

describe("publicBriefOnly", () => {
  it("strips gated headings", () => {
    const publicText = publicBriefOnly(
      "# Public\n\nHello from the public cut.\n\n## Gated full answers (behind watchlist login)\n\nSECRET\n",
    );
    expect(publicText).toContain("Hello from the public cut.");
    expect(publicText).not.toContain("SECRET");
    expect(publicText).not.toContain("Gated");
  });
});
