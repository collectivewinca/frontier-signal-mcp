# Privacy policy — Frontier Signal MCP

**Effective date:** 3 November 2026
**Operator:** VE Lab ([velab.org](https://velab.org/))
**Product:** Frontier Signal MCP
**Support:** [hello@velab.org](mailto:hello@velab.org) · [alet@velab.org](mailto:alet@velab.org)

This policy covers the **public Frontier Signal MCP** (stdio package and the HTTPS Streamable HTTP endpoint). It does **not** cover the gated watchlist at [velab.org/frontier-signal/watchlist](https://velab.org/frontier-signal/watchlist).

## What this service is

Frontier Signal MCP is a **public, read-only** query interface over verified AI data-broker buyer programmes and demand signals that VE Lab already publishes. There is **no login**, **no API key**, and **no account**.

Tools return data from committed public baselines. They do not invent hit counts, URLs, or programmes, and they do not serve gated watchlist answers.

## Data we process

| Kind | What happens |
| --- | --- |
| Tool arguments | Optional filters such as a programme name or an `observed` date. Used only to look up public rows. Not used to build a profile. |
| MCP protocol traffic | JSON-RPC requests to `/mcp` (initialize, list tools, call tools). |
| Connection metadata | The HTTPS endpoint is hosted on Cloudflare Workers. Cloudflare may process IP address, user-agent, and standard request logs as described in [Cloudflare’s privacy policy](https://www.cloudflare.com/privacypolicy/). |
| Accounts / cookies | None. We do not set cookies, do not run ads, and do not require an identity. |

We do **not** ask for names, emails, company records you want to sell, or any personal data. Do not send personal data in tool arguments.

## Data we publish

Responses contain **public verified programme data**: names, URLs, payout bands, referral copy, categories, statuses, demand-mix mention counts (heuristics, not search-engine hit counts), public briefs, and change notes. That corpus is also in this repository under `data/`.

## What we do not do

- Authenticate callers or store user accounts
- Expose gated watchlist content
- Sell, rent, or share query logs with data brokers
- Invent hit counts or unpublished prices
- Track users across sites

## Retention

The Worker is stateless. Tool calls are not written to a VE Lab database. Cloudflare may retain operational logs for a limited period under its own policy. Local stdio usage never leaves your machine.

## Children

This service is not directed at children under 16.

## Changes

We will update this page and the dated file in the repository when the policy changes.

## Contact

Questions: [hello@velab.org](mailto:hello@velab.org). You may also write [alet@velab.org](mailto:alet@velab.org).

Public product pages: [Frontier Signal](https://velab.org/frontier-signal/) · [weekly brief](https://velab.org/frontier-signal/brief/).
