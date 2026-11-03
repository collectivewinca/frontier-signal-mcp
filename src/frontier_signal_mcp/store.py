"""Load and query committed Frontier Signal baselines and public briefs."""

from __future__ import annotations

import json
import os
import re
from difflib import SequenceMatcher
from pathlib import Path

from frontier_signal_mcp.brief import public_brief_only
from frontier_signal_mcp.models import (
    Baseline,
    BriefResult,
    DeltasResult,
    DemandMix,
    ObservedDates,
    ProgrammeDetail,
    ProgrammeList,
    ProgrammeLookup,
    ProgrammeSummary,
    Source,
)

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TOKEN_RE = re.compile(r"[a-z0-9]+")
FUZZY_THRESHOLD = 0.72


class SignalError(ValueError):
    """User-facing lookup error (unknown date, missing brief, etc.)."""


def resolve_data_dir(explicit: Path | str | None = None) -> Path:
    """Locate data/baselines relative to env, install, or repo checkout."""
    if explicit is not None:
        path = Path(explicit).expanduser().resolve()
        _require_baselines(path)
        return path
    env = os.environ.get("FRONTIER_SIGNAL_DATA_DIR")
    if env:
        path = Path(env).expanduser().resolve()
        _require_baselines(path)
        return path
    here = Path(__file__).resolve().parent
    candidates = [
        here / "data",
        here.parents[1] / "data",
        here.parents[2] / "data" if len(here.parents) >= 2 else None,
        Path.cwd() / "data",
    ]
    for candidate in candidates:
        if candidate is None:
            continue
        if (candidate / "baselines").is_dir():
            return candidate.resolve()
    raise FileNotFoundError(
        "Frontier Signal data directory not found. Set FRONTIER_SIGNAL_DATA_DIR "
        "or keep data/baselines in the repo checkout."
    )


def _require_baselines(path: Path) -> None:
    if not (path / "baselines").is_dir():
        raise FileNotFoundError(
            f"{path} has no baselines/ directory. Drop JSON cuts in "
            "data/baselines/YYYY-MM-DD.json."
        )


def _tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.casefold())


def _score_name(query: str, name: str) -> tuple[float, str]:
    q = query.casefold().strip()
    n = name.casefold().strip()
    if not q or not n:
        return 0.0, "none"
    if q == n:
        return 1.0, "exact"
    if q in n or n in q:
        return 0.92, "substring"
    q_tokens = _tokens(q)
    n_tokens = _tokens(n)
    if q_tokens and all(token in n_tokens for token in q_tokens):
        return 0.88, "substring"
    ratio = SequenceMatcher(None, q, n).ratio()
    for token in n_tokens:
        ratio = max(ratio, SequenceMatcher(None, q, token).ratio())
    if ratio >= FUZZY_THRESHOLD:
        return ratio, "fuzzy"
    return ratio, "none"


def _summary(source: Source, observed: str) -> ProgrammeSummary:
    return ProgrammeSummary(
        name=source.name,
        url=source.url,
        band=source.band,
        referral=source.referral,
        categories=source.categories,
        status=source.status,
        notes=source.notes,
        type=source.type,
        observed=observed,
        checked=source.checked,
    )


class SignalStore:
    """File-backed store. Reloads when baseline/brief mtimes change."""

    def __init__(self, data_dir: Path | str | None = None) -> None:
        self.data_dir = resolve_data_dir(data_dir)
        self._baselines: dict[str, Baseline] = {}
        self._briefs: dict[str, tuple[float, str]] = {}
        self._baseline_mtimes: dict[str, float] = {}
        self._scan()

    @property
    def baselines_dir(self) -> Path:
        return self.data_dir / "baselines"

    @property
    def briefs_dir(self) -> Path:
        return self.data_dir / "briefs"

    def _scan(self) -> None:
        self._load_baselines()
        self._load_briefs()

    def _load_baselines(self) -> None:
        seen: set[str] = set()
        if not self.baselines_dir.is_dir():
            self._baselines = {}
            self._baseline_mtimes = {}
            return
        for path in sorted(self.baselines_dir.glob("*.json")):
            mtime = path.stat().st_mtime
            cached = self._baselines.get(path.stem)
            prev_mtime = self._baseline_mtimes.get(str(path))
            if cached is not None and prev_mtime == mtime:
                seen.add(cached.observed)
                continue
            raw = json.loads(path.read_text(encoding="utf-8"))
            baseline = Baseline.model_validate(raw)
            if not DATE_RE.match(baseline.observed):
                raise SignalError(
                    f"{path.name} has observed={baseline.observed!r}; "
                    "expected YYYY-MM-DD"
                )
            self._baselines[baseline.observed] = baseline
            self._baseline_mtimes[str(path)] = mtime
            seen.add(baseline.observed)
        stale = [key for key in self._baselines if key not in seen]
        for key in stale:
            del self._baselines[key]

    def _load_briefs(self) -> None:
        seen: set[str] = set()
        if not self.briefs_dir.is_dir():
            self._briefs = {}
            return
        for path in sorted(self.briefs_dir.glob("*.md")):
            stem = path.stem
            if not DATE_RE.match(stem):
                continue
            mtime = path.stat().st_mtime
            cached = self._briefs.get(stem)
            if cached is not None and cached[0] == mtime:
                seen.add(stem)
                continue
            public = public_brief_only(path.read_text(encoding="utf-8"))
            self._briefs[stem] = (mtime, public)
            seen.add(stem)
        stale = [key for key in self._briefs if key not in seen]
        for key in stale:
            del self._briefs[key]

    def refresh(self) -> None:
        self._scan()

    def dates(self) -> list[str]:
        self.refresh()
        return sorted(self._baselines.keys(), reverse=True)

    def brief_dates(self) -> list[str]:
        self.refresh()
        return sorted(self._briefs.keys(), reverse=True)

    def latest_date(self) -> str:
        dates = self.dates()
        if not dates:
            raise SignalError(
                "No baselines found. Drop a JSON cut in data/baselines/YYYY-MM-DD.json."
            )
        return dates[0]

    def get_baseline(self, observed: str | None = None) -> Baseline:
        self.refresh()
        date = (observed or "").strip() or self.latest_date()
        if not DATE_RE.match(date):
            raise SignalError(
                f"observed must be YYYY-MM-DD, got {observed!r}. "
                f"Available: {', '.join(self.dates()) or '(none)'}"
            )
        baseline = self._baselines.get(date)
        if baseline is None:
            available = ", ".join(self.dates()) or "(none)"
            raise SignalError(
                f"No baseline for {date}. Available dates: {available}"
            )
        return baseline

    def list_observed_dates(self) -> ObservedDates:
        dates = self.dates()
        briefs = self.brief_dates()
        return ObservedDates(
            dates=dates,
            latest=dates[0] if dates else None,
            brief_dates=briefs,
            latest_brief=briefs[0] if briefs else None,
        )

    def list_programmes(
        self,
        *,
        type: str | None = None,
        status: str | None = None,
        category: str | None = None,
        observed: str | None = None,
    ) -> ProgrammeList:
        baseline = self.get_baseline(observed)
        type_filter = (type or "").strip().casefold() or None
        status_filter = (status or "").strip().casefold() or None
        category_filter = (category or "").strip().casefold() or None
        matched: list[ProgrammeSummary] = []
        for source in baseline.sources:
            if type_filter and source.type.casefold() != type_filter:
                continue
            if status_filter and source.status.casefold() != status_filter:
                continue
            if category_filter and category_filter not in source.categories.casefold():
                continue
            matched.append(_summary(source, baseline.observed))
        return ProgrammeList(
            observed=baseline.observed,
            programme_count=len(matched),
            programmes=matched,
            filters={
                "type": type.strip() if type and type.strip() else None,
                "status": status.strip() if status and status.strip() else None,
                "category": category.strip() if category and category.strip() else None,
            },
        )

    def get_programme(
        self,
        name: str,
        observed: str | None = None,
    ) -> ProgrammeLookup:
        query = (name or "").strip()
        baseline = self.get_baseline(observed)
        if not query:
            return ProgrammeLookup(
                query=query,
                observed=baseline.observed,
                match_kind="none",
                message="Pass a programme name to look up. Nothing was invented.",
            )
        ranked: list[tuple[float, str, Source]] = []
        for source in baseline.sources:
            score, kind = _score_name(query, source.name)
            if kind == "none":
                continue
            ranked.append((score, kind, source))
        if not ranked:
            return ProgrammeLookup(
                query=query,
                observed=baseline.observed,
                match_kind="none",
                message=(
                    f"No programme matching {query!r} on {baseline.observed}. "
                    "Names are taken from the baseline; this tool does not invent programmes."
                ),
            )
        ranked.sort(key=lambda row: (-row[0], row[2].name.casefold()))
        best_score, best_kind, best = ranked[0]
        alternatives = [
            source.name
            for score, kind, source in ranked[1:]
            if score >= min(best_score, FUZZY_THRESHOLD) or kind in {"exact", "substring"}
        ]
        detail = ProgrammeDetail(
            **_summary(best, baseline.observed).model_dump(),
            browser=best.browser,
        )
        return ProgrammeLookup(
            query=query,
            observed=baseline.observed,
            match_kind=best_kind,
            match=detail,
            alternatives=alternatives,
        )

    def demand_mix(self, observed: str | None = None) -> DemandMix:
        baseline = self.get_baseline(observed)
        return DemandMix(
            observed=baseline.observed,
            hot=list(baseline.hot),
            hot_note=baseline.hot_note,
        )

    def deltas(self, observed: str | None = None) -> DeltasResult:
        baseline = self.get_baseline(observed)
        return DeltasResult(
            observed=baseline.observed,
            deltas_vs_prev=list(baseline.deltas_vs_prev),
            recheck=baseline.recheck,
        )

    def latest_brief(self, observed: str | None = None) -> BriefResult:
        self.refresh()
        if observed and observed.strip():
            date = observed.strip()
            if not DATE_RE.match(date):
                raise SignalError(
                    f"observed must be YYYY-MM-DD, got {observed!r}. "
                    f"Available briefs: {', '.join(self.brief_dates()) or '(none)'}"
                )
        else:
            briefs = self.brief_dates()
            if not briefs:
                raise SignalError(
                    "No public briefs found. Drop markdown in "
                    "data/briefs/YYYY-MM-DD.md (public cut only)."
                )
            date = briefs[0]
        entry = self._briefs.get(date)
        if entry is None:
            available = ", ".join(self.brief_dates()) or "(none)"
            raise SignalError(
                f"No public brief for {date}. Available briefs: {available}"
            )
        markdown = entry[1]
        if not markdown.strip():
            raise SignalError(
                f"Brief {date} was empty after stripping gated watchlist content. "
                "This server never serves gated copy."
            )
        return BriefResult(
            observed=date,
            markdown=markdown,
            public_only=True,
            path=str(self.briefs_dir / f"{date}.md"),
        )


_STORE: SignalStore | None = None


def get_store() -> SignalStore:
    global _STORE
    if _STORE is None:
        _STORE = SignalStore()
    return _STORE


def reset_store() -> None:
    """Drop the process-wide store (tests)."""
    global _STORE
    _STORE = None
