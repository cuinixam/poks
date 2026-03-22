"""Download and extraction progress reporting for Poks."""

import threading
from collections.abc import Callable

from rich.console import Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

ProgressCallback = Callable[[str, int, int | None], None]
# Signature: (app_name, current, total_or_none)


class RichProgressHandler:
    """Rich-based progress display with separate download and extraction bars grouped in a single live display."""

    def __init__(self) -> None:
        self._download_tasks: dict[str, TaskID] = {}
        self._extract_tasks: dict[str, TaskID] = {}
        self._lock = threading.Lock()

        self._download_progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        )
        self._extract_progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
        )

        self._live: Live | None = None

    def _ensure_live(self) -> None:
        """Ensure the single Live context is running."""
        if self._live is None:
            group = Group(self._download_progress, self._extract_progress)
            self._live = Live(group, refresh_per_second=10)
            self._live.start()

    def close(self) -> None:
        """Stop the live display. Call this after all work is done."""
        with self._lock:
            if self._live is not None:
                self._live.stop()
                self._live = None

    def on_download(self, app_name: str, downloaded: int, total: int | None) -> None:
        """Report download progress for an app."""
        with self._lock:
            self._ensure_live()
            if app_name not in self._download_tasks:
                self._download_tasks[app_name] = self._download_progress.add_task(app_name, total=total or 0)
            task_id = self._download_tasks[app_name]

            if total is not None and self._download_progress.tasks[task_id].total != total:
                self._download_progress.update(task_id, total=total)
            self._download_progress.update(task_id, completed=downloaded)

    def on_extract(self, app_name: str, extracted: int, total: int | None) -> None:
        """Report extraction progress for an app."""
        with self._lock:
            self._ensure_live()
            desc = f"Unpack {app_name}"
            if app_name not in self._extract_tasks:
                self._extract_tasks[app_name] = self._extract_progress.add_task(desc, total=total or 0)
            task_id = self._extract_tasks[app_name]

            if total is not None and self._extract_progress.tasks[task_id].total != total:
                self._extract_progress.update(task_id, total=total)
            self._extract_progress.update(task_id, completed=extracted)


default_progress = RichProgressHandler()
