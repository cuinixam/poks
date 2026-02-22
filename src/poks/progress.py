"""Download progress reporting for Poks."""

import threading
from collections.abc import Callable

from rich.progress import BarColumn, DownloadColumn, Progress, TaskID, TimeRemainingColumn, TransferSpeedColumn

ProgressCallback = Callable[[str, int, int | None], None]
# Signature: (app_name, bytes_downloaded, total_bytes_or_none)


class RichProgressHandler:
    """Rich-based progress display that manages per-app download bars."""

    def __init__(self) -> None:
        self._progress: Progress | None = None
        self._tasks: dict[str, TaskID] = {}
        self._lock = threading.Lock()

    def __call__(self, app_name: str, downloaded: int, total: int | None) -> None:
        with self._lock:
            if self._progress is None:
                self._progress = Progress(
                    "[progress.description]{task.description}",
                    BarColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                )
                self._progress.start()
            if app_name not in self._tasks:
                self._tasks[app_name] = self._progress.add_task(app_name, total=total or 0)
            task_id = self._tasks[app_name]
        if total and self._progress.tasks[task_id].total != total:
            self._progress.update(task_id, total=total)
        self._progress.update(task_id, completed=downloaded)
        if total and downloaded >= total:
            with self._lock:
                self._tasks.pop(app_name, None)
                if not self._tasks:
                    self._progress.stop()
                    self._progress = None


default_progress = RichProgressHandler()
