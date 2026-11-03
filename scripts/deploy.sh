#!/usr/bin/env bash
# Deploy the public Frontier Signal MCP Worker (Streamable HTTP).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/worker"

if [[ ! -d node_modules ]]; then
  npm ci
fi

npm run embed-data
npx wrangler types
npm test

echo
echo "Deploying frontier-signal-mcp to Cloudflare Workers…"
echo "Account: ${CLOUDFLARE_ACCOUNT_ID:-aa6789c67f992fd0b9f5933e86e11184}"
echo "Preferred custom domain (after DNS): https://mcp.velab.org/mcp"
echo

npx wrangler deploy "$@"

echo
echo "Optional custom domain (zone must be in this account):"
echo "  npx wrangler deploy --x-route-zones --domain mcp.velab.org"
echo "Privacy page: https://<worker>.<subdomain>.workers.dev/privacy"
