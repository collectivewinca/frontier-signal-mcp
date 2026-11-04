from __future__ import annotations

import json
from pathlib import Path

import pytest

from frontier_signal_mcp.brief import public_brief_only
from frontier_signal_mcp.models import Baseline
from frontier_signal_mcp.store import SignalError, SignalStore


def test_parse_all_committed_baselines(data_dir: Path) -> None:
    files = sorted((data_dir / "baselines").glob("*.json"))
    assert [path.name for path in files] == [
        "2026-10-30.json",
        "2026-11-02.json",
        "2026-11-03.json",
        "2026-11-04.json",
    ]
    expected_sources = {
        "2026-10-30.json": 24,
        "2026-11-02.json": 24,
        "2026-11-03.json": 24,
        "2026-11-04.json": 25,
    }
    for path in files:
        raw = json.loads(path.read_text(encoding="utf-8"))
        baseline = Baseline.model_validate(raw)
        assert baseline.observed == path.stem
        assert len(baseline.sources) == expected_sources[path.name]
        assert len(baseline.hot) == 9
        assert baseline.hot[0].category == "Software / code"
        assert baseline.hot[0].mention_count == 12
        assert baseline.deltas_vs_prev


def test_optional_recheck_field(data_dir: Path) -> None:
    store = SignalStore(data_dir)
    assert store.get_baseline("2026-10-30").recheck is None
    assert store.get_baseline("2026-11-02").recheck is None
    assert store.get_baseline("2026-11-03").recheck


def test_list_programmes_filters(store: SignalStore) -> None:
    all_rows = store.list_programmes(observed="2026-11-03")
    assert all_rows.programme_count == 24
    buyers = store.list_programmes(type="buyer", observed="2026-11-03")
    assert buyers.programme_count == 17
    assert all(row.type == "buyer" for row in buyers.programmes)
    legal = store.list_programmes(
        type="buyer",
        category="legal",
        observed="2026-11-03",
    )
    names = {row.name for row in legal.programmes}
    assert "Handshake AI" in names
    assert "Nyne" in names
    assert "Mode / BizBuyData" in names
    dead = store.list_programmes(status="dead", observed="2026-11-03")
    assert {row.name for row in dead.programmes} == {"HUMXN", "Grepped"}
    empty = store.list_programmes(category="no-such-category-xyz")
    assert empty.programme_count == 0
    assert empty.programmes == []


def test_get_programme_exact_and_fuzzy(store: SignalStore) -> None:
    exact = store.get_programme("Handshake AI", observed="2026-11-03")
    assert exact.match_kind == "exact"
    assert exact.match is not None
    assert exact.match.url == "https://joinhandshake.com/ai/"
    assert exact.match.band == "$100K–$4M+"

    fuzzy = store.get_programme("lazarus")
    assert fuzzy.match_kind in {"substring", "fuzzy"}
    assert fuzzy.match is not None
    assert fuzzy.match.name == "Turing (Lazarus)"
    assert "50K" in fuzzy.match.referral

    missing = store.get_programme("not-a-real-programme-zzz")
    assert missing.match_kind == "none"
    assert missing.match is None
    assert "does not invent" in (missing.message or "")


def test_demand_mix_matches_json_and_does_not_invent(
    store: SignalStore, data_dir: Path
) -> None:
    raw = json.loads(
        (data_dir / "baselines" / "2026-11-03.json").read_text(encoding="utf-8")
    )
    mix = store.demand_mix("2026-11-03")
    assert mix.observed == "2026-11-03"
    assert [(row.category, row.mention_count) for row in mix.hot] == [
        tuple(pair) for pair in raw["hot"]
    ]
    assert "not" in mix.disclaimer.lower()
    assert "hit count" in mix.disclaimer.lower()
    assert mix.hot_note and "heuristic" in mix.hot_note.lower()


def test_deltas_latest(store: SignalStore) -> None:
    result = store.deltas()
    assert result.observed == "2026-11-04"
    assert any("Patronus" in note for note in result.deltas_vs_prev)
    assert any("micro1" in note for note in result.deltas_vs_prev)
    assert result.recheck


def test_list_observed_dates(store: SignalStore) -> None:
    dates = store.list_observed_dates()
    assert dates.dates == ["2026-11-04", "2026-11-03", "2026-11-02", "2026-10-30"]
    assert dates.latest == "2026-11-04"
    assert dates.brief_dates == ["2026-11-04", "2026-11-03"]
    assert dates.latest_brief == "2026-11-04"


def test_unknown_date_lists_available(store: SignalStore) -> None:
    with pytest.raises(SignalError, match="Available"):
        store.get_baseline("2020-01-01")


def test_latest_brief_is_public_only(store: SignalStore) -> None:
    brief = store.latest_brief()
    assert brief.observed == "2026-11-04"
    assert brief.public_only is True
    assert "Public brief" in brief.markdown
    assert "Patronus AI" in brief.markdown
    assert "Lazarus" in brief.markdown
    assert "Gated full answers" not in brief.markdown
    assert "Implied capability" not in brief.markdown
    assert "Preferred source profiles" not in brief.markdown


def test_public_brief_strips_gated_heading() -> None:
    raw = (
        "# Public\n\nHello from the public cut.\n\n"
        "## Gated full answers (behind watchlist login)\n\nSECRET\n"
    )
    public = public_brief_only(raw)
    assert "Hello from the public cut." in public
    assert "SECRET" not in public
    assert "Gated" not in public


def test_store_strips_gated_brief_on_disk(tmp_path: Path, data_dir: Path) -> None:
    baselines = tmp_path / "baselines"
    briefs = tmp_path / "briefs"
    baselines.mkdir()
    briefs.mkdir()
    (baselines / "2026-11-03.json").write_text(
        (data_dir / "baselines" / "2026-11-03.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (briefs / "2026-11-03.md").write_text(
        "# Cut\n\nPublic paragraph.\n\n## Gated watchlist\n\nmember-only\n",
        encoding="utf-8",
    )
    isolated = SignalStore(tmp_path)
    brief = isolated.latest_brief("2026-11-03")
    assert "Public paragraph." in brief.markdown
    assert "member-only" not in brief.markdown
