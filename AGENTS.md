# AGENTS.md

Guidance for coding agents working on this repository.

## What this is

A public, read-only MCP for VE Lab Frontier Signal: verified AI data-broker buyer programmes and demand signals.

Two runtimes share the same public corpus under `data/`:

- **stdio:** Python FastMCP (`src/frontier_signal_mcp/`) for Cursor / Claude Desktop.
- **HTTPS remote:** Cloudflare Worker (`worker/`) with `createMcpHandler` (Streamable HTTP at `/mcp`) for Claude Connectors, ChatGPT Apps, and the Official MCP Registry `remotes` field.

Brand: [VE Lab / Frontier Signal](https://velab.org/frontier-signal/).

## Commands

```bash
uv sync
uv run pytest
uv run python -m frontier_signal_mcp

cd worker
npm ci
npm test
npx wrangler deploy
bash scripts/deploy.sh
```

Python `>=3.11`. Do not add runtime secrets, network fetches, or auth. Public read-only is the product.

## Layout

- `src/frontier_signal_mcp/server.py` — FastMCP tools (`title` + `readOnlyHint` required)
- `src/frontier_signal_mcp/store.py` — load / filter / lookup
- `worker/src/index.ts` — Streamable HTTP MCP + `/privacy` + `/health`
- `worker/src/store.ts` — same query semantics as Python
- `worker/scripts/embed-data.mjs` — bake `data/` + `docs/privacy.md` into `worker/src/embedded.ts`
- `data/baselines/YYYY-MM-DD.json` — daily public JSON cuts
- `data/briefs/YYYY-MM-DD.md` — public brief markdown only
- `docs/privacy.md` — public privacy policy
- `server.json` — Registry metadata (`packages` + `remotes`)

## Invariants (do not break)

1. **Never invent hit counts.** `demand_mix` returns `hot` exactly as recorded.
2. **Never expose gated watchlist content.** `latest_brief` must run markdown through `public_brief_only` / `publicBriefOnly`.
3. **Never invent programmes, URLs, or prices.** Misses are empty lists / `match_kind=none` / date errors that list available dates.
4. **Public verified data only.** No PII, no credentials, no third-party API keys.
5. **Every tool** has a human `title` and `readOnlyHint: true` (also copy the title into `annotations.title` for Claude’s directory check).
6. **Offline corpus.** Python reads files; the Worker serves the last `embed-data` snapshot. Do not fetch velab.org or aidata.broker at runtime.

## Dropping in a newer daily baseline

1. Write `data/baselines/YYYY-MM-DD.json` with `observed` matching the filename.
2. Write `data/briefs/YYYY-MM-DD.md` with the **public** brief only.
3. `uv run pytest` and `cd worker && npm test`.
4. Redeploy the Worker so remotes pick up the new cut.

## Packaging / listing

- MIT in `pyproject.toml` and `LICENSE`.
- Registry name: `io.github.collectivewinca/frontier-signal-mcp`.
- Remote URL in `server.json`: `https://mcp.velab.org/mcp`.
- Support: hello@velab.org / alet@velab.org.
- Privacy URL: `/privacy` on the Worker (source: `docs/privacy.md`).
- Do not claim a store listing that does not exist yet.
