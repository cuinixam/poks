"""Archive extraction for Poks."""

from __future__ import annotations

import shutil
import tarfile
import zipfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Literal, cast

import py7zr

SUPPORTED_FORMATS: dict[str, str] = {
    ".zip": "zip",
    ".tar.gz": "tar:gz",
    ".tgz": "tar:gz",
    ".tar.xz": "tar:xz",
    ".txz": "tar:xz",
    ".tar.bz2": "tar:bz2",
    ".tbz2": "tar:bz2",
    ".7z": "7z",
}


def _detect_format(archive_path: Path) -> str:
    """Return the format key for the given archive path based on its suffix(es)."""
    name = archive_path.name.lower()
    for ext, fmt in SUPPORTED_FORMATS.items():
        if name.endswith(ext):
            return fmt
    supported = ", ".join(sorted(SUPPORTED_FORMATS.keys()))
    raise ValueError(f"Unsupported archive format: {archive_path.name}. Supported: {supported}")


def _validate_entry_paths(names: list[str], dest_dir: Path) -> None:
    """Reject archive entries that would escape *dest_dir* via path traversal."""
    resolved_dest = dest_dir.resolve()
    for name in names:
        target = (dest_dir / name).resolve()
        if not target.is_relative_to(resolved_dest):
            raise ValueError(f"Path traversal detected in archive entry: {name!r}")


@contextmanager
def _open_archive(archive_path: Path, fmt: str) -> Generator[Any, None, None]:
    """Open an archive file and yield the archive object."""
    if fmt == "zip":
        with zipfile.ZipFile(archive_path) as zf:
            yield zf
    elif fmt == "7z":
        with py7zr.SevenZipFile(archive_path, mode="r") as sz:
            yield sz
    else:
        tar_mode = cast(Literal["r:gz", "r:xz", "r:bz2"], f"r:{fmt.split(':')[1]}")
        with tarfile.open(archive_path, tar_mode) as tf:
            yield tf


def _extract_all(archive: Any, fmt: str, dest_dir: Path) -> None:
    """Extract all contents of an archive into dest_dir after validating paths."""
    if fmt == "zip":
        _validate_entry_paths(archive.namelist(), dest_dir)
        archive.extractall(dest_dir)  # noqa: S202 — entry paths validated above
    elif fmt == "7z":
        _validate_entry_paths(archive.getnames(), dest_dir)
        archive.extractall(path=dest_dir)  # noqa: S202 — entry paths validated above
    elif hasattr(tarfile, "data_filter"):
        archive.extractall(dest_dir, filter="data")
    else:
        _validate_entry_paths([member.name for member in archive.getmembers()], dest_dir)
        archive.extractall(dest_dir)  # noqa: S202 — entry paths validated above


def _relocate_extract_dir(dest_dir: Path, extract_dir: str) -> None:
    """Move contents of dest_dir/extract_dir into dest_dir."""
    source = dest_dir / extract_dir
    if not source.resolve().is_relative_to(dest_dir.resolve()):
        raise ValueError(f"extract_dir '{extract_dir}' escapes destination directory")
    if not source.is_dir():
        raise ValueError(f"extract_dir '{extract_dir}' not found in extracted archive")
    for item in source.iterdir():
        shutil.move(str(item), str(dest_dir / item.name))
    source.rmdir()


def extract_archive(archive_path: Path, dest_dir: Path, extract_dir: str | None = None) -> Path:
    """Extract an archive into *dest_dir* and return *dest_dir*."""
    fmt = _detect_format(archive_path)
    dest_dir.mkdir(parents=True, exist_ok=True)
    with _open_archive(archive_path, fmt) as archive:
        _extract_all(archive, fmt, dest_dir)
    if extract_dir:
        _relocate_extract_dir(dest_dir, extract_dir)
    return dest_dir
