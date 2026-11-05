from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastmcp import Client

from frontier_signal_mcp.server import mcp


EXPECTED_TOOLS = {
    "list_buyer_programmes",
    "get_programme",
    "demand_mix",
    "latest_brief",
    "deltas",
    "list_observed_dates",
}


def _payload(result: object) -> dict:
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, dict):
        return structured
    data = getattr(result, "data", None)
    if isinstance(data, dict):
        return data
    if hasattr(data, "model_dump"):
        dumped = data.model_dump()
        if isinstance(dumped, dict):
            return dumped
    content = getattr(result, "content", None)
    if content:
        text = getattr(content[0], "text", None)
        if text:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
    raise AssertionError(f"Could not read tool payload from {result!r}")


@pytest.mark.asyncio
async def test_tools_registered() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()
    names = {tool.name for tool in tools}
    assert EXPECTED_TOOLS <= names
    for tool in tools:
        if tool.name not in EXPECTED_TOOLS:
            continue
        title = getattr(tool, "title", None)
        annotations = getattr(tool, "annotations", None)
        ann_title = None
        read_only = None
        if annotations is not None:
            ann_title = getattr(annotations, "title", None)
            if isinstance(annotations, dict):
                ann_title = annotations.get("title")
                read_only = annotations.get("readOnlyHint", annotations.get("read_only_hint"))
            else:
                read_only = getattr(annotations, "read_only_hint", None)
                if read_only is None:
                    read_only = getattr(annotations, "readOnlyHint", None)
        assert title or ann_title, f"{tool.name} is missing a title"
        assert read_only is True, f"{tool.name} must set readOnlyHint"


@pytest.mark.asyncio
async def test_list_observed_dates_tool_happy_path() -> None:
    async with Client(mcp) as client:
        payload = _payload(await client.call_tool("list_observed_dates", {}))
    assert payload["latest"] == "2026-11-05"
    assert payload["dates"][0] == "2026-11-05"
    assert "2026-10-30" in payload["dates"]


@pytest.mark.asyncio
async def test_list_buyer_programmes_and_demand_mix_tools() -> None:
    async with Client(mcp) as client:
        programmes = _payload(
            await client.call_tool(
                "list_buyer_programmes",
                {
                    "type": "buyer",
                    "category": "healthcare",
                    "observed": "2026-11-03",
                },
            )
        )
        mix = _payload(await client.call_tool("demand_mix", {}))
        lookup = _payload(
            await client.call_tool("get_programme", {"name": "micro1"})
        )
    assert programmes["observed"] == "2026-11-03"
    assert programmes["programme_count"] >= 1
    names = {row["name"] for row in programmes["programmes"]}
    assert "Scale AI" in names
    assert mix["hot"][0]["category"] == "Software / code"
    assert mix["hot"][0]["mention_count"] == 12
    assert lookup["match"]["name"] == "micro1"
    assert lookup["match_kind"] in {"exact", "substring"}


@pytest.mark.asyncio
async def test_unknown_date_is_an_error_not_invented() -> None:
    async with Client(mcp) as client:
        with pytest.raises(Exception, match="No baseline"):
            await client.call_tool("demand_mix", {"observed": "1999-01-01"})


def test_package_data_present(data_dir: Path) -> None:
    assert (data_dir / "baselines" / "2026-11-03.json").is_file()
    assert (data_dir / "briefs" / "2026-11-03.md").is_file()
    assert (data_dir / "baselines" / "2026-11-04.json").is_file()
    assert (data_dir / "briefs" / "2026-11-04.md").is_file()
    assert (data_dir / "baselines" / "2026-11-05.json").is_file()
    assert (data_dir / "briefs" / "2026-11-05.md").is_file()
