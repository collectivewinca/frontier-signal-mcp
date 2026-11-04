# Frontier Signal MCP

Query **verified** AI data-broker buyer programmes and demand signals from [VE Lab](https://velab.org/) [Frontier Signal](https://velab.org/frontier-signal/).

Public and read-only. No API keys, no login, no gated watchlist. Tools never invent hit counts.

<!-- mcp-name: io.github.collectivewinca/frontier-signal-mcp -->

Live surfaces:

- **Remote MCP (Streamable HTTP):** `https://mcp.velab.org/mcp` (preferred custom domain after deploy; `*.workers.dev` is the v1 fallback)
- **Privacy policy:** [docs/privacy.md](docs/privacy.md) · hosted at `/privacy` on the same Worker
- Product: [velab.org/frontier-signal](https://velab.org/frontier-signal/)
- Public weekly brief: [velab.org/frontier-signal/brief](https://velab.org/frontier-signal/brief/)
- Gated watchlist (not exposed here): [velab.org/frontier-signal/watchlist](https://velab.org/frontier-signal/watchlist)

## What it does

One verb: **query** verified buyer programmes and demand signals.

| Tool | Title | Returns |
| --- | --- | --- |
| `list_buyer_programmes` | List buyer programmes | Sources from a baseline, optional filters `type`, `status`, `category`. Fields: name, url, band, referral, categories, status, notes. |
| `get_programme` | Get a programme | One source by exact or fuzzy name. |
| `demand_mix` | Demand mix | Hot categories (`[category, mention_count]`) for latest or a given `observed` date. |
| `latest_brief` | Latest public brief | Public brief markdown for latest or a date. Gated sections are stripped. |
| `deltas` | Baseline deltas | `deltas_vs_prev` (and `recheck` if present) for latest or a date. |
| `list_observed_dates` | List observed dates | Baseline dates (and public brief dates) in this checkout. |

Every tool sets `title` and `readOnlyHint: true` (Claude Connectors / ChatGPT Apps requirement). Mention counts on `demand_mix` are **heuristics recorded on the baseline**, not search-engine hit counts.

## Remote HTTPS MCP

This is the path for **Official MCP Registry remotes**, **Claude custom connectors**, and **ChatGPT Apps**.

| | |
| --- | --- |
| Transport | Streamable HTTP |
| Endpoint | `https://mcp.velab.org/mcp` |
| Privacy | `https://mcp.velab.org/privacy` |
| Auth | None (public read-only) |
| Worker | `worker/` (Cloudflare Workers + `createMcpHandler`) |

If `mcp.velab.org` is not yet attached, the Worker also publishes `https://frontier-signal-mcp.<your-subdomain>.workers.dev/mcp`. After `wrangler deploy`, Wrangler prints the live URL — use that until the custom domain is on.

### Hit the remote URL

```bash
# Health
curl -sS https://mcp.velab.org/health

# MCP initialize (Streamable HTTP)
curl -sS https://mcp.velab.org/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}'
```

Cursor (remote):

```json
{
  "mcpServers": {
    "frontier-signal": {
      "url": "https://mcp.velab.org/mcp"
    }
  }
}
```

### Claude custom connector — test steps

1. Open [claude.ai](https://claude.ai) → **Settings** → **Connectors** (or **Custom connectors**).
2. **Add custom connector**.
3. Name: `Frontier Signal`.
4. URL: `https://mcp.velab.org/mcp` (or the `workers.dev` URL from deploy).
5. Authentication: **No authentication**.
6. Save and enable the connector for a chat.
7. Ask: *Using Frontier Signal, list observed dates and then the demand mix. Do not invent extra mention counts.*
8. Confirm Claude calls `list_observed_dates` then `demand_mix`. Latest cut should be `2026-11-04` in this checkout; Software / code mention count is **12** (heuristic, not a hit count).
9. Optional: *Look up Lazarus* → `get_programme` returns **Turing (Lazarus)**. *Show the public brief* → `latest_brief` must not include gated watchlist copy.

### ChatGPT Apps / Connectors

1. Create or edit the app / custom GPT.
2. Add an MCP server / connector with URL `https://mcp.velab.org/mcp`.
3. No OAuth client ID or secret.
4. Smoke the same prompts as the Claude steps above.
5. Point the app’s privacy URL at `https://mcp.velab.org/privacy`.

## Listing materials (Registry, Claude, ChatGPT)

| Field | Copy |
| --- | --- |
| **One-liner** | Query verified AI data-broker buyer programmes and demand signals. |
| **Description** | Frontier Signal is VE Lab’s public, read-only MCP for daily baselines of AI data-buyer programmes, demand mix, and public briefs. No login. Does not invent hit counts or expose the gated watchlist. |
| **Support** | [hello@velab.org](mailto:hello@velab.org) (also [alet@velab.org](mailto:alet@velab.org)) |
| **Privacy policy** | https://mcp.velab.org/privacy |
| **Homepage** | https://velab.org/frontier-signal/ |
| **MCP URL** | https://mcp.velab.org/mcp |
| **Icon / brand** | VE Lab / Frontier Signal — [velab.org](https://velab.org/) |

`server.json` lists the Streamable HTTP remote plus the local PyPI/stdio package. Registry publish is still a later step (`mcp-publisher`).

## Local stdio (Cursor / Claude Desktop)

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/collectivewinca/frontier-signal-mcp
cd frontier-signal-mcp
uv sync
uv run python -m frontier_signal_mcp
```

Equivalent: `uv run frontier-signal-mcp`.

### Cursor (`~/.cursor/mcp.json` or project `.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "frontier-signal": {
      "command": "uv",
      "args": [
        "--directory",
        "/ABSOLUTE/PATH/to/frontier-signal-mcp",
        "run",
        "python",
        "-m",
        "frontier_signal_mcp"
      ]
    }
  }
}
```

### Claude Desktop (`claude_desktop_config.json`)

Same `command` / `args` as Cursor, under `mcpServers.frontier-signal`.

## Deploy the Worker

Cloudflare account used by VE Lab Workers: `aa6789c67f992fd0b9f5933e86e11184` (set as `account_id` in `worker/wrangler.jsonc`).

```bash
cd worker
npm ci
npm test
npx wrangler login          # or: export CLOUDFLARE_API_TOKEN=...
npx wrangler deploy         # prints https://frontier-signal-mcp.<subdomain>.workers.dev
```

This environment has no Cloudflare API token, so production is not published from the PR agent. Config is `worker/wrangler.jsonc` (Wrangler 4; equivalent to wrangler.toml). After login, the commands above are the whole deploy.

Or from repo root: `bash scripts/deploy.sh`.

Attach the preferred host **after** the Worker exists and the `velab.org` zone is in this account:

```bash
cd worker
npx wrangler deploy --x-route-zones --domain mcp.velab.org
```

Then confirm:

- `https://mcp.velab.org/mcp` — Streamable HTTP
- `https://mcp.velab.org/privacy` — this policy
- `https://mcp.velab.org/health` — `{ ok: true, ... }`

Local Worker: `cd worker && npm run dev` then `http://127.0.0.1:8787/mcp`.

Dropping in a newer daily baseline: add files under `data/`, run `npm run embed-data` in `worker/`, redeploy. The Python stdio server picks up new files on the next tool call without a rebuild.

## Data (offline from the repo)

```
data/baselines/YYYY-MM-DD.json
data/briefs/YYYY-MM-DD.md
```

Sample cuts: `2026-10-30`, `2026-11-02`, `2026-11-03`, `2026-11-04` (plus public briefs for `2026-11-03` and `2026-11-04`).

1. Copy the day’s JSON to `data/baselines/YYYY-MM-DD.json` (`observed` must match the filename).
2. Copy **only the public brief** to `data/briefs/YYYY-MM-DD.md`. Stop before any gated / watchlist-login heading.
3. Stdio: restart the MCP client if needed. Remote: `cd worker && npm run embed-data && npx wrangler deploy`.

Override the Python data directory with `FRONTIER_SIGNAL_DATA_DIR=/path/to/data`.

## Privacy

Full policy: [docs/privacy.md](docs/privacy.md) (rendered at `/privacy` on the Worker).

- **Public verified data only.** No PII, no credentials, no API keys.
- **No gated watchlist content.** `latest_brief` strips gated headings.
- **No invented hit counts.** `demand_mix` returns the `hot` array as recorded.
- **No auth** is correct for this product.

## Distribution intent (10-store)

1. **Official MCP Registry** — `server.json` name `io.github.collectivewinca/frontier-signal-mcp`, with `remotes` (Streamable HTTP) and `packages` (stdio).
2. **ChatGPT Apps** and **Claude Connectors** (custom connector URL above).
3. Then Google Connected Apps, Grok, Cursor Marketplace, Meta Muse, Copilot Agent Store, AgentExchange, AWS Marketplace.

This repo is not yet submitted to those stores.

## Development

```bash
uv sync
uv run pytest
cd worker && npm ci && npm test
```

See [AGENTS.md](AGENTS.md) for invariants and [CHANGELOG.md](CHANGELOG.md) for releases.

## License

[MIT](LICENSE)
