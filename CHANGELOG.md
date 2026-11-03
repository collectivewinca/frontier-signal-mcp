# Changelog

All notable changes to Frontier Signal MCP are documented in this file.

## 0.1.0 — 2026-11-03

### Added

- Public, read-only FastMCP server over committed VE Lab Frontier Signal baselines.
- Tools: `list_buyer_programmes`, `get_programme`, `demand_mix`, `latest_brief`, `deltas`, `list_observed_dates`.
- Sample data: `data/baselines/2026-10-30.json`, `2026-11-02.json`, `2026-11-03.json`, and the public brief `data/briefs/2026-11-03.md`.
- Gated-watchlist stripper so `latest_brief` never serves login-only copy.
- stdio entry (`python -m frontier_signal_mcp` / `frontier-signal-mcp`) plus a documented `--transport http` remote path.
- `server.json` stub for Official MCP Registry (`io.github.collectivewinca/frontier-signal-mcp`).
