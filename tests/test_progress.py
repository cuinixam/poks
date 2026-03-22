"""Unit tests for the progress display module."""

from __future__ import annotations

from typing import Any

import pytest

import poks.progress
from poks.progress import RichProgressHandler


class DummyLive:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


def test_live_starts_on_first_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(poks.progress, "Live", DummyLive)
    handler = RichProgressHandler()
    assert handler._live is None

    handler.on_download("app1", 0, 100)

    assert handler._live is not None
    assert handler._live.started is True  # type: ignore[unreachable]


def test_live_stays_open_until_close(monkeypatch: pytest.MonkeyPatch) -> None:
    """Live display is not auto-stopped when tasks complete — only close() stops it."""
    monkeypatch.setattr(poks.progress, "Live", DummyLive)
    handler = RichProgressHandler()

    handler.on_download("app1", 0, 100)
    handler.on_extract("app1", 0, 50)

    handler.on_download("app1", 100, 100)
    handler.on_extract("app1", 50, 50)

    # Live is still open after all tasks complete
    assert handler._live is not None
    assert handler._live.stopped is False  # type: ignore[attr-defined]

    # Explicit close stops it
    handler.close()
    assert handler._live is None


def test_close_is_safe_when_no_live(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(poks.progress, "Live", DummyLive)
    handler = RichProgressHandler()
    handler.close()  # Should not raise


def test_multiple_apps_tracked_independently(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(poks.progress, "Live", DummyLive)
    handler = RichProgressHandler()

    handler.on_download("app1", 10, 100)
    handler.on_download("app2", 20, 200)

    assert len(handler._download_tasks) == 2

    # Both apps complete — tasks stay tracked (Live stays open until close())
    handler.on_download("app1", 100, 100)
    handler.on_download("app2", 200, 200)
    assert handler._live is not None

    handler.close()


def test_download_and_extract_bars_separate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(poks.progress, "Live", DummyLive)
    handler = RichProgressHandler()

    handler.on_download("app1", 50, 100)
    handler.on_extract("app1", 3, 10)

    assert len(handler._download_tasks) == 1
    assert len(handler._extract_tasks) == 1

    handler.close()
