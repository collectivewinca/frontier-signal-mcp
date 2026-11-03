/** Strip gated watchlist content from brief markdown before serving. */

const GATED_HEADING = /^#{1,6}\s+.*\bgated\b.*$/im;
const WATCHLIST_ONLY = /^#{1,6}\s+.*\bwatchlist\b.*\b(login|members?|gated)\b.*$/im;
const TRAILING_RULE = /(?:\r?\n)-{3,}\s*$/;

export function publicBriefOnly(markdown: string): string {
  let text = markdown.replace(/\r\n/g, "\n");
  let cutAt: number | undefined;
  for (const pattern of [GATED_HEADING, WATCHLIST_ONLY]) {
    const match = pattern.exec(text);
    if (match && (cutAt === undefined || match.index < cutAt)) {
      cutAt = match.index;
    }
  }
  if (cutAt !== undefined) {
    text = text.slice(0, cutAt);
  }
  text = text.replace(TRAILING_RULE, "").replace(/\s+$/, "");
  return text ? `${text}\n` : "";
}
