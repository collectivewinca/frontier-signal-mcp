import { PRIVACY_MARKDOWN } from "./embedded";

export const PRODUCT_URL = "https://velab.org/frontier-signal/";
export const BRIEF_URL = "https://velab.org/frontier-signal/brief/";
export const SUPPORT_EMAIL = "hello@velab.org";
export const SUPPORT_EMAIL_ALT = "alet@velab.org";

const STYLE = `
  :root { color-scheme: dark; }
  body { font-family: ui-sans-serif, system-ui, sans-serif; margin: 0; background: #0b0d10; color: #e8eaed; line-height: 1.55; }
  main { max-width: 44rem; margin: 0 auto; padding: 2.5rem 1.25rem 4rem; }
  a { color: #9ecbff; }
  h1 { font-size: 1.75rem; margin: 0 0 0.5rem; }
  h2 { font-size: 1.15rem; margin-top: 1.75rem; }
  .lede { color: #b7bcc4; }
  code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.9em; }
  pre { background: #161a20; padding: 0.9rem 1rem; overflow: auto; border-radius: 8px; }
  .chip { display: inline-block; border: 1px solid #2c3340; border-radius: 999px; padding: 0.15rem 0.7rem; font-size: 0.8rem; color: #c5cad3; margin-right: 0.4rem; }
  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: left; border-bottom: 1px solid #232833; padding: 0.4rem 0.35rem; vertical-align: top; }
  footer { margin-top: 2.5rem; color: #8b919a; font-size: 0.9rem; }
`;

function htmlPage(title: string, body: string): Response {
  const html = `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${title}</title>
  <style>${STYLE}</style>
</head>
<body>
  <main>${body}</main>
</body>
</html>`;
  return new Response(html, {
    headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "public, max-age=300",
      "x-content-type-options": "nosniff",
    },
  });
}

function escapeHtml(text: string): string {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderMarkdownLite(markdown: string): string {
  const lines = markdown.replace(/\r\n/g, "\n").split("\n");
  const out: string[] = [];
  let inTable = false;
  let inList = false;
  const flushList = () => {
    if (inList) {
      out.push("</ul>");
      inList = false;
    }
  };
  const flushTable = () => {
    if (inTable) {
      out.push("</tbody></table>");
      inTable = false;
    }
  };
  const inline = (text: string): string => {
    const escaped = escapeHtml(text);
    return escaped
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");
  };
  for (const line of lines) {
    if (line.startsWith("| ")) {
      flushList();
      const cells = line
        .split("|")
        .slice(1, -1)
        .map((cell) => cell.trim());
      if (cells.every((cell) => /^:?-{3,}:?$/.test(cell))) continue;
      if (!inTable) {
        out.push("<table><tbody>");
        inTable = true;
        out.push(`<tr>${cells.map((cell) => `<th>${inline(cell)}</th>`).join("")}</tr>`);
      } else {
        out.push(`<tr>${cells.map((cell) => `<td>${inline(cell)}</td>`).join("")}</tr>`);
      }
      continue;
    }
    flushTable();
    if (line.startsWith("# ")) {
      flushList();
      out.push(`<h1>${inline(line.slice(2))}</h1>`);
    } else if (line.startsWith("## ")) {
      flushList();
      out.push(`<h2>${inline(line.slice(3))}</h2>`);
    } else if (line.startsWith("- ")) {
      if (!inList) {
        out.push("<ul>");
        inList = true;
      }
      out.push(`<li>${inline(line.slice(2))}</li>`);
    } else if (line.trim() === "") {
      flushList();
    } else {
      flushList();
      out.push(`<p>${inline(line)}</p>`);
    }
  }
  flushList();
  flushTable();
  return out.join("\n");
}

export function landingPage(request: Request): Response {
  const origin = new URL(request.url).origin;
  const mcpUrl = `${origin}/mcp`;
  const privacyUrl = `${origin}/privacy`;
  const body = `
    <p class="chip">VE Lab</p><p class="chip">public · read-only · no auth</p>
    <h1>Frontier Signal MCP</h1>
    <p class="lede">Query verified AI data-broker buyer programmes and demand signals. Streamable HTTP. Never invents hit counts. Never serves gated watchlist copy.</p>
    <p><strong>MCP endpoint</strong></p>
    <pre>${escapeHtml(mcpUrl)}</pre>
    <p>
      <a href="${escapeHtml(mcpUrl)}">/mcp</a> ·
      <a href="${escapeHtml(privacyUrl)}">Privacy policy</a> ·
      <a href="${PRODUCT_URL}">Product</a> ·
      <a href="${BRIEF_URL}">Weekly brief</a>
    </p>
    <h2>Tools</h2>
    <table>
      <tr><th>Tool</th><th>Title</th></tr>
      <tr><td><code>list_buyer_programmes</code></td><td>List buyer programmes</td></tr>
      <tr><td><code>get_programme</code></td><td>Get a programme</td></tr>
      <tr><td><code>demand_mix</code></td><td>Demand mix</td></tr>
      <tr><td><code>latest_brief</code></td><td>Latest public brief</td></tr>
      <tr><td><code>deltas</code></td><td>Baseline deltas</td></tr>
      <tr><td><code>list_observed_dates</code></td><td>List observed dates</td></tr>
    </table>
    <h2>Claude / ChatGPT</h2>
    <p>Add a custom connector with URL <code>${escapeHtml(mcpUrl)}</code>. No OAuth. See the repository README for the full test steps.</p>
    <footer>Support: <a href="mailto:${SUPPORT_EMAIL}">${SUPPORT_EMAIL}</a> · <a href="mailto:${SUPPORT_EMAIL_ALT}">${SUPPORT_EMAIL_ALT}</a></footer>
  `;
  return htmlPage("Frontier Signal MCP", body);
}

export function privacyHtml(): Response {
  return htmlPage(
    "Privacy policy — Frontier Signal MCP",
    `${renderMarkdownLite(PRIVACY_MARKDOWN)}
     <footer><a href="/">Back to Frontier Signal MCP</a></footer>`,
  );
}

export function privacyMarkdown(): Response {
  return new Response(PRIVACY_MARKDOWN, {
    headers: {
      "content-type": "text/markdown; charset=utf-8",
      "cache-control": "public, max-age=300",
    },
  });
}
