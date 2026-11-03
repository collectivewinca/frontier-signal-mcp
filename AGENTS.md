# AGENTS.md

Guidance for coding agents working on this repository.

## What this is

A public, read-only Python MCP server (FastMCP + uv) that lets an agent **query** VE Lab Frontier Signal baselines: verified AI data-broker buyer programmes and demand signals.

Brand: [VE Lab / Frontier Signal](https://velab.org/frontier-signal/). Product source of truth lives in the committed JSON under `data/baselines/` and the public briefs under `data/briefs/`.

## Commands

```bash
uv sync
uv run pytest
uv run python -m frontier_signal_mcp
uv run python -m frontier_signal_mcp --transport http --port 8000
```

Python `>=3.11`. Do not add runtime secrets, network fetches, or auth.

## Layout

- `src/frontier_signal_mcp/server.py` — FastMCP tools and `main()`
- `src/frontier_signal_mcp/store.py` — load / filter / lookup
- `src/frontier_signal_mcp/models.py` — baseline + tool result shapes
- `src/frontier_signal_mcp/brief.py` — strip gated watchlist markdown
- `data/baselines/YYYY-MM-DD.json` — daily public JSON cuts
- `data/briefs/YYYY-MM-DD.md` — public brief markdown only
- `tests/` — parse baselines + at least one tool happy path

## Invariants (do not break)

1. **Never invent hit counts.** `demand_mix` returns `hot` exactly as recorded. If `hot` is missing, return an empty list, not guessed numbers. Keep the disclaimer that mention counts are heuristics, not hit counts.
2. **Never expose gated watchlist content.** `latest_brief` must run markdown through `public_brief_only`. Do not commit watchlist-only answers under `data/briefs/`. The live gated surface is https://velab.org/frontier-signal/watchlist — out of scope.
3. **Never invent programmes, URLs, or prices.** A filter miss is an empty list. A name miss is `match_kind=none`. An unknown date is an error that lists available dates.
4. **Public verified data only.** No PII, no credentials, no third-party API keys. Tools are read-only (`readOnlyHint`).
5. **Offline from the repo.** The server reads local files. Do not silently fetch velab.org or aidata.broker at runtime in v1.

## Dropping in a newer daily baseline

1. Write `data/baselines/YYYY-MM-DD.json` with `observed` matching the filename.
2. Write `data/briefs/YYYY-MM-DD.md` with the **public** brief only (cut before any `## Gated` / watchlist-login heading).
3. Run `uv run pytest`. Confirm `list_observed_dates` picks up the new `observed` value.
4. Do not “fill in” missing bands, referral figures, or mention counts.

## Tool contracts

| Tool | Default date | Notes |
| --- | --- | --- |
| `list_buyer_programmes` | latest baseline | Optional `type` (buyer/lab/seed), exact `status`, category substring. |
| `get_programme` | latest baseline | Exact, then substring, then fuzzy (`difflib`). |
| `demand_mix` | latest baseline | Copy `hot` + `hot_note`. |
| `latest_brief` | latest **brief** file | Public markdown only. |
| `deltas` | latest baseline | Copy `deltas_vs_prev`; do not recompute a diff. |
| `list_observed_dates` | n/a | Dates present on disk. |

Keep the set small (these six). New tools need a product reason.

## Packaging

- MIT license in `pyproject.toml` and `LICENSE`.
- Registry name: `io.github.collectivewinca/frontier-signal-mcp` (`server.json` + `mcp-name` HTML comment in README).
- Distribution intent: Official MCP Registry first, then ChatGPT Apps + Claude Connectors, then the rest of the 10-store list. Do not claim a store listing that does not exist yet.
