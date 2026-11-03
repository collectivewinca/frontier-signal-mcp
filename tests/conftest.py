from __future__ import annotations

from pathlib import Path

import pytest

from frontier_signal_mcp.store import SignalStore, reset_store

REPO_ROOT = Path(__file__).resolve().parents[1]
REPO_DATA = REPO_ROOT / "data"


@pytest.fixture
def data_dir() -> Path:
    return REPO_DATA


@pytest.fixture
def store(data_dir: Path) -> SignalStore:
    return SignalStore(data_dir)


@pytest.fixture(autouse=True)
def _reset_singleton() -> None:
    reset_store()
    yield
    reset_store()
