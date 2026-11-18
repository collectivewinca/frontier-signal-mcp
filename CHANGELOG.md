# Changelog

All notable changes to Frontier Signal MCP are documented in this file.

## Unreleased

### Changed

- Removed the internal "AIData licence" line (member-answer handling guidance) from the 2026-11-16 baseline `recheck` text, so the `deltas` tool no longer serves it. Regenerated `worker/src/embedded.ts`.

### Added

- Added the 2026-11-16 baseline and public brief, so the MCP matches the Nov 16 weekly brief on velab.org (44 buyers, 32 with a public figure; company-records middle half $149K–$537K, was $150K–$548K; tasks and environments $49–$102 with a seventh buyer; expert work $54–$104). Regenerated `worker/src/embedded.ts`. The source cut stored `recheck` as an object; it is committed as a single string (`key: value; ...`) because the Python model and Worker expect a string. Python tests updated for the new latest date.
- Added the 2026-11-05 baseline and public brief (AIData board company-records middle half widened to $131K–$548K; Handshake calculator default $400K–$800K+ per the board; micro1 referral packages $100K–$3M+; AfterQuery floor read as 10+ people / 3+ years).
- Added the 2026-11-04 baseline and public brief (Patronus AI buyer, micro1 band widen, and board/lab drift).

## 0.2.0 — 2026-11-03

### Added

- Public HTTPS remote MCP on a Cloudflare Worker (`worker/`) using `createMcpHandler` and Streamable HTTP at `/mcp`.
- Privacy policy at [docs/privacy.md](docs/privacy.md), served as HTML at `/privacy` and markdown at `/privacy.md`.
- `server.json` `remotes` entry for `https://mcp.velab.org/mcp` (keep stdio `packages`).
- Tool `title` plus `annotations.title` and `readOnlyHint` on all six tools (Python and Worker).
- README listing materials, Claude custom connector test steps, and Worker deploy commands.
- `scripts/deploy.sh` and `worker/wrangler.jsonc`.

## 0.1.0 — 2026-11-03

### Added

- Public, read-only FastMCP server over committed VE Lab Frontier Signal baselines.
- Tools: `list_buyer_programmes`, `get_programme`, `demand_mix`, `latest_brief`, `deltas`, `list_observed_dates`.
- Sample data: `data/baselines/2026-10-30.json`, `2026-11-02.json`, `2026-11-03.json`, and the public brief `data/briefs/2026-11-03.md`.
- Gated-watchlist stripper so `latest_brief` never serves login-only copy.
- stdio entry (`python -m frontier_signal_mcp` / `frontier-signal-mcp`) plus a documented `--transport http` remote path.
- `server.json` stub for Official MCP Registry (`io.github.collectivewinca/frontier-signal-mcp`).
