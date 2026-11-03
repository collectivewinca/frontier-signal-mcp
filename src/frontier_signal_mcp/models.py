"""Pydantic models for Frontier Signal public baselines and tool results."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


MENTION_COUNT_DISCLAIMER = (
    "Mention counts are heuristics recorded on the public baseline, not "
    "search-engine hit counts. Do not invent additional counts."
)


class BrowserCheck(BaseModel):
    """Optional browser-side verification attached to a source."""

    model_config = ConfigDict(extra="ignore")

    status: str | None = None
    facts: list[str] = Field(default_factory=list)
    notes: str | None = None
    observed: str | None = None


class Source(BaseModel):
    """One verified programme, lab board, or seed source from a baseline."""

    model_config = ConfigDict(extra="ignore")

    name: str
    type: str
    url: str
    status: str
    categories: str = ""
    band: str = ""
    referral: str = ""
    notes: str = ""
    checked: str | None = None
    browser: BrowserCheck | None = None


class HotCategory(BaseModel):
    """One demand-mix row as recorded on the baseline (not a hit count)."""

    category: str
    mention_count: int


class Baseline(BaseModel):
    """One daily public baseline JSON cut."""

    model_config = ConfigDict(extra="ignore")

    observed: str
    sources: list[Source]
    hot: list[HotCategory] = Field(default_factory=list)
    deltas_vs_prev: list[str] = Field(default_factory=list)
    hot_note: str | None = None
    recheck: str | None = None

    @field_validator("hot", mode="before")
    @classmethod
    def coerce_hot(cls, value: Any) -> Any:
        if not value:
            return []
        coerced: list[Any] = []
        for item in value:
            if isinstance(item, dict):
                coerced.append(item)
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                coerced.append(
                    {"category": item[0], "mention_count": item[1]},
                )
            else:
                raise ValueError(
                    "hot entries must be [category, mention_count] pairs; "
                    "refusing to invent a count"
                )
        return coerced


class ProgrammeSummary(BaseModel):
    """Public fields returned by list_buyer_programmes."""

    name: str
    url: str
    band: str
    referral: str
    categories: str
    status: str
    notes: str
    type: str
    observed: str
    checked: str | None = None


class ProgrammeList(BaseModel):
    observed: str
    programme_count: int
    programmes: list[ProgrammeSummary]
    filters: dict[str, str | None]


class ProgrammeDetail(ProgrammeSummary):
    """Single-programme lookup, including optional browser facts."""

    browser: BrowserCheck | None = None


class ProgrammeLookup(BaseModel):
    query: str
    observed: str
    match_kind: str
    match: ProgrammeDetail | None = None
    alternatives: list[str] = Field(default_factory=list)
    message: str | None = None


class DemandMix(BaseModel):
    observed: str
    hot: list[HotCategory]
    hot_note: str | None = None
    disclaimer: str = MENTION_COUNT_DISCLAIMER


class DeltasResult(BaseModel):
    observed: str
    deltas_vs_prev: list[str]
    recheck: str | None = None


class BriefResult(BaseModel):
    observed: str
    markdown: str
    public_only: bool = True
    path: str | None = None
    message: str | None = None


class ObservedDates(BaseModel):
    dates: list[str]
    latest: str | None
    brief_dates: list[str]
    latest_brief: str | None = None
