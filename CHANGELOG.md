# Changelog

All notable changes to Frontier Signal MCP are documented in this file.

## Unreleased

### Added

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
