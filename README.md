# Frontier Signal MCP

Query **verified** AI data-broker buyer programmes and demand signals from [VE Lab](https://velab.org/) [Frontier Signal](https://velab.org/frontier-signal/).

This is a Python MCP server (FastMCP + uv). v1 is public and read-only. It serves committed daily baselines from this repo so an agent can work **offline** — no API keys, no login, no gated watchlist.

<!-- mcp-name: io.github.collectivewinca/frontier-signal-mcp -->

Live surfaces:

- Product: [velab.org/frontier-signal](https://velab.org/frontier-signal/)
- Public weekly brief: [velab.org/frontier-signal/brief](https://velab.org/frontier-signal/brief/)
- Gated watchlist (not exposed here): [velab.org/frontier-signal/watchlist](https://velab.org/frontier-signal/watchlist)

## What it does

One verb: **query** verified buyer programmes and demand signals.

| Tool | Returns |
| --- | --- |
| `list_buyer_programmes` | Sources from a baseline, optional filters `type`, `status`, `category`. Fields: name, url, band, referral, categories, status, notes. |
| `get_programme` | One source by exact or fuzzy name. |
| `demand_mix` | Hot categories (`[category, mention_count]`) for latest or a given `observed` date. |
| `latest_brief` | Public brief markdown for latest or a date. Gated sections are stripped. |
| `deltas` | `deltas_vs_prev` (and `recheck` if present) for latest or a date. |
| `list_observed_dates` | Baseline dates (and public brief dates) in this checkout. |

Mention counts on `demand_mix` are **heuristics recorded on the baseline**, not search-engine hit counts. Tools never invent counts, URLs, or programmes. If a date is missing they say so and list what *is* available.

## Install

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/collectivewinca/frontier-signal-mcp
cd frontier-signal-mcp
uv sync
```

Run the server (stdio, the default):

```bash
uv run python -m frontier_signal_mcp
```

Equivalent entry points:

```bash
uv run frontier-signal-mcp
uv run fastmcp run src/frontier_signal_mcp/server.py:mcp
```

Documented remote path (not required for v1):

```bash
uv run python -m frontier_signal_mcp --transport http --host 127.0.0.1 --port 8000
```

Put a TLS reverse proxy in front of that before exposing it to ChatGPT Apps or Claude Connectors. v1 itself does not authenticate; treat the HTTP transport as public read-only.

## Cursor / Claude / ChatGPT config

Replace `/ABSOLUTE/PATH/to/frontier-signal-mcp` with the clone path.

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

### ChatGPT (Apps / Connectors)

ChatGPT's connector path wants a **remote** MCP URL, not stdio.

1. Run `--transport http` behind HTTPS (see above).
2. Point the ChatGPT app or connector at `https://your-host/mcp`.
3. No secrets to configure — this server has none.

Until that host exists, use Cursor or Claude Desktop with the stdio snippet. Distribution order is Registry first, then ChatGPT + Claude (see below).

## Data (offline from the repo)

Baselines and public briefs ship in-tree so the server does not fetch the network:

```
data/baselines/YYYY-MM-DD.json
data/briefs/YYYY-MM-DD.md
```

Sample cuts in this checkout: `2026-10-30`, `2026-11-02`, `2026-11-03` (plus the public brief for `2026-11-03`).

### Drop in a newer daily baseline

1. Copy the day's JSON to `data/baselines/YYYY-MM-DD.json`. The filename date should match the `observed` field.
2. Copy **only the public brief** to `data/briefs/YYYY-MM-DD.md`. Stop before any heading that says gated / watchlist-login. Do not add watchlist-only answers.
3. Restart the MCP client (the store also reloads on mtime, so a running stdio server will pick up new files on the next tool call).

Override the data directory with `FRONTIER_SIGNAL_DATA_DIR=/path/to/data` if you keep cuts outside the package.

Schema (source of truth: the JSON itself):

- `observed` (YYYY-MM-DD)
- `sources[]`: `name`, `type`, `url`, `status`, `categories`, `band`, `referral`, `notes`, `checked`, optional `browser`
- `hot[]`: `[category, mention_count]` pairs
- `deltas_vs_prev[]`, `hot_note`, optional `recheck`

## Privacy

- **Public verified data only.** Programmes, bands, and briefs in this repo are the public Frontier Signal cuts.
- **No PII, no credentials, no API keys.** The server does not authenticate and does not call third-party APIs.
- **No gated watchlist content.** `latest_brief` strips headings that mark gated / watchlist-login copy. Do not commit that copy under `data/briefs/`.
- **No invented hit counts.** `demand_mix` returns the `hot` array as recorded. Agents must not add counts.

## Distribution intent (10-store)

v1 is a stdio server with a documented HTTP path. Intended store order:

1. **Official MCP Registry** (first) — `server.json` uses `io.github.collectivewinca/frontier-signal-mcp`. Publish the PyPI package, then `mcp-publisher`. The README contains the required `mcp-name` marker.
2. **ChatGPT Apps** and **Claude Connectors** (fast approval path).
3. Then Google Connected Apps, Grok, Cursor Marketplace, Meta Muse, Copilot Agent Store, AgentExchange, AWS Marketplace.

This scaffold is not yet submitted to those stores.

## Development

```bash
uv sync
uv run pytest
uv run python -m frontier_signal_mcp --help
```

See [AGENTS.md](AGENTS.md) for invariants and [CHANGELOG.md](CHANGELOG.md) for releases.

## License

[MIT](LICENSE)
