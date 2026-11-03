"""Frontier Signal MCP server — public, read-only tools over committed baselines."""

from __future__ import annotations

import argparse
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from frontier_signal_mcp import __version__
from frontier_signal_mcp.models import (
    BriefResult,
    DeltasResult,
    DemandMix,
    ObservedDates,
    ProgrammeList,
    ProgrammeLookup,
)
from frontier_signal_mcp.store import SignalError, get_store

INSTRUCTIONS = """
You are querying VE Lab Frontier Signal: verified AI data-broker buyer
programmes and demand signals.

Rules:
- Use only values returned by these tools. Never invent hit counts, URLs,
  programmes, prices, or job counts.
- Mention counts in demand_mix are heuristics recorded on the baseline,
  not search-engine hit counts.
- This server is public and read-only. It does not expose gated watchlist
  content. Do not ask it for login-only answers.
- If a date is missing, report the available dates from list_observed_dates.
""".strip()

def _annotations(title: str) -> dict[str, object]:
    """Claude Connectors want annotations.title + readOnlyHint on every tool."""
    return {
        "title": title,
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }

mcp = FastMCP(
    "Frontier Signal",
    instructions=INSTRUCTIONS,
    version=__version__,
)


def _raise(exc: SignalError) -> None:
    raise SignalError(str(exc)) from exc


@mcp.tool(
    title="List buyer programmes",
    annotations=_annotations("List buyer programmes"),
)
def list_buyer_programmes(
    type: Annotated[
        str | None,
        Field(
            description="Filter by source type: buyer, lab, or seed. Omit for all.",
        ),
    ] = None,
    status: Annotated[
        str | None,
        Field(
            description=(
                "Filter by exact status (case-insensitive), e.g. ok, browser-ok, "
                "dead, board-only, 200."
            ),
        ),
    ] = None,
    category: Annotated[
        str | None,
        Field(
            description="Substring match against the categories field (case-insensitive).",
        ),
    ] = None,
    observed: Annotated[
        str | None,
        Field(
            description="Baseline date YYYY-MM-DD. Omit for the latest committed cut.",
        ),
    ] = None,
) -> ProgrammeList:
    """List verified buyer programmes (and other sources) from a public baseline.

    Returns name, url, band, referral, categories, status, notes, and type.
    Filters are optional. An empty list means no rows matched — programmes
    are never invented.
    """
    try:
        return get_store().list_programmes(
            type=type,
            status=status,
            category=category,
            observed=observed,
        )
    except SignalError as exc:
        _raise(exc)
        raise


@mcp.tool(
    title="Get a programme",
    annotations=_annotations("Get a programme"),
)
def get_programme(
    name: Annotated[
        str,
        Field(description="Programme name to look up (exact, substring, or fuzzy)."),
    ],
    observed: Annotated[
        str | None,
        Field(
            description="Baseline date YYYY-MM-DD. Omit for the latest committed cut.",
        ),
    ] = None,
) -> ProgrammeLookup:
    """Look up one verified programme by exact or fuzzy name.

    Prefer exact and substring matches. If several names match, the best
    hit is returned and others are listed as alternatives. A miss returns
    match_kind=none — this tool does not invent a programme.
    """
    try:
        return get_store().get_programme(name, observed=observed)
    except SignalError as exc:
        _raise(exc)
        raise


@mcp.tool(
    title="Demand mix",
    annotations=_annotations("Demand mix"),
)
def demand_mix(
    observed: Annotated[
        str | None,
        Field(
            description="Baseline date YYYY-MM-DD. Omit for the latest committed cut.",
        ),
    ] = None,
) -> DemandMix:
    """Return hot demand categories recorded on a public baseline.

    mention_count values are heuristics copied from the JSON cut, not hit
    counts. This tool never invents additional categories or counts.
    """
    try:
        return get_store().demand_mix(observed=observed)
    except SignalError as exc:
        _raise(exc)
        raise


@mcp.tool(
    title="Latest public brief",
    annotations=_annotations("Latest public brief"),
)
def latest_brief(
    observed: Annotated[
        str | None,
        Field(
            description="Brief date YYYY-MM-DD. Omit for the latest public brief.",
        ),
    ] = None,
) -> BriefResult:
    """Return the public Frontier Signal brief markdown for a date.

    Only the public cut is served. Gated watchlist sections are stripped
    if present. Missing dates are reported; a brief is never synthesised.
    """
    try:
        return get_store().latest_brief(observed=observed)
    except SignalError as exc:
        _raise(exc)
        raise


@mcp.tool(
    title="Baseline deltas",
    annotations=_annotations("Baseline deltas"),
)
def deltas(
    observed: Annotated[
        str | None,
        Field(
            description="Baseline date YYYY-MM-DD. Omit for the latest committed cut.",
        ),
    ] = None,
) -> DeltasResult:
    """Return deltas_vs_prev (and recheck notes, if any) for a baseline cut.

    These are the change notes recorded on that JSON file versus the
    previous cut. This tool does not compute new diffs.
    """
    try:
        return get_store().deltas(observed=observed)
    except SignalError as exc:
        _raise(exc)
        raise


@mcp.tool(
    title="List observed dates",
    annotations=_annotations("List observed dates"),
)
def list_observed_dates() -> ObservedDates:
    """List baseline dates (and public brief dates) available in this checkout.

    Dates come from filenames and the observed field. No live fetch is
    performed.
    """
    return get_store().list_observed_dates()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Frontier Signal MCP server (public verified baselines).",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "http"),
        default="stdio",
        help="stdio for Cursor/Claude Desktop; http for a later remote path.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)
    run_kwargs: dict[str, Any] = {"transport": args.transport}
    if args.transport == "http":
        run_kwargs["host"] = args.host
        run_kwargs["port"] = args.port
    mcp.run(**run_kwargs)


if __name__ == "__main__":
    main()
