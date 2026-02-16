"""Convert Scoop manifests to Poks manifests."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any

from py_app_dev.core.logging import logger

from poks.domain.models import PoksAppVersion, PoksArchive, PoksManifest

SCOOP_ARCH_MAP: dict[str, tuple[str, str]] = {
    "64bit": ("windows", "x86_64"),
    "32bit": ("windows", "x86"),
    "arm64": ("windows", "aarch64"),
}

UNCONVERTIBLE_FIELDS = (
    "post_install",
    "pre_install",
    "pre_uninstall",
    "post_uninstall",
    "installer",
    "uninstaller",
    "shortcuts",
    "persist",
    "psmodule",
    "notes",
    "depends",
    "suggest",
    "innosetup",
    "checkver",
    "autoupdate",
)


def _as_list(value: str | list[str]) -> list[str]:
    if isinstance(value, str):
        return [value]
    return value


def _extract_license(raw: str | dict[str, str] | None) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw.get("identifier")
    return raw


def _extract_ext(url: str) -> str | None:
    """Extract file extension from URL for the archive."""
    path = url.split("?")[0].split("#")[0]
    suffixes = Path(path).suffixes
    if not suffixes:
        return None
    # Handle compound extensions like .tar.gz
    if len(suffixes) >= 2 and suffixes[-2] == ".tar":
        return "".join(suffixes[-2:])
    return suffixes[-1]


def _collect_bin_dirs(scoop_data: dict[str, Any]) -> list[str] | None:
    """Collect bin_dirs from env_add_path and bin fields."""
    dirs: list[str] = []
    env_add_path = scoop_data.get("env_add_path")
    if env_add_path is not None:
        dirs.extend(_as_list(env_add_path))

    bin_field = scoop_data.get("bin")
    if bin_field is not None:
        for entry in _as_list(bin_field):
            parent = str(PurePosixPath(entry).parent)
            if parent != "." and parent not in dirs:
                dirs.append(parent)
        # If bins are in root dir and no other dirs collected, add "."
        if not dirs and bin_field:
            return None

    return dirs if dirs else None


def _convert_arch_entry(
    arch_data: dict[str, Any],
    target_os: str,
    target_arch: str,
    version_extract_dir: str | None,
    version_bin_dirs: list[str] | None,
) -> PoksArchive:
    url = str(arch_data["url"])
    sha256 = str(arch_data["hash"])
    ext = _extract_ext(url)

    arch_extract_dir = arch_data.get("extract_dir")
    arch_bin_dirs = _collect_bin_dirs(arch_data)

    return PoksArchive(
        os=target_os,
        arch=target_arch,
        url=url,
        sha256=sha256,
        ext=ext,
        extract_dir=str(arch_extract_dir) if arch_extract_dir and arch_extract_dir != version_extract_dir else None,
        bin_dirs=arch_bin_dirs if arch_bin_dirs != version_bin_dirs else None,
    )


def convert_scoop_manifest(scoop_path: Path) -> PoksManifest:
    """Convert a Scoop manifest JSON file to a PoksManifest."""
    scoop_data = json.loads(scoop_path.read_text(encoding="utf-8"))

    # Warn about unconvertible fields
    for field_name in UNCONVERTIBLE_FIELDS:
        if field_name in scoop_data:
            logger.warning(f"Scoop field '{field_name}' has no Poks equivalent and will be skipped.")

    description = scoop_data.get("description", "")
    version_str = scoop_data.get("version", "0.0.0")
    homepage = scoop_data.get("homepage")
    license_str = _extract_license(scoop_data.get("license"))

    raw_extract_dir = scoop_data.get("extract_dir")
    version_extract_dir: str | None = str(raw_extract_dir) if raw_extract_dir is not None else None
    version_bin_dirs = _collect_bin_dirs(scoop_data)

    archives: list[PoksArchive] = []
    architecture = scoop_data.get("architecture")

    if architecture:
        for scoop_arch, (poks_os, poks_arch) in SCOOP_ARCH_MAP.items():
            arch_data = architecture.get(scoop_arch)
            if not arch_data:
                continue
            archives.append(_convert_arch_entry(arch_data, poks_os, poks_arch, version_extract_dir, version_bin_dirs))
    elif "url" in scoop_data:
        url = scoop_data["url"]
        sha256 = scoop_data.get("hash", "")
        # Top-level URL: single archive, assume windows x86_64
        if isinstance(url, list):
            url = url[0]
            sha256 = sha256[0] if isinstance(sha256, list) else sha256
        archives.append(
            PoksArchive(
                os="windows",
                arch="x86_64",
                url=url,
                sha256=sha256,
                ext=_extract_ext(url),
            )
        )

    env: dict[str, str] | None = scoop_data.get("env_set")

    app_version = PoksAppVersion(
        version=version_str,
        archives=archives,
        extract_dir=version_extract_dir,
        bin_dirs=version_bin_dirs,
        env=env,
    )

    return PoksManifest(
        description=description,
        versions=[app_version],
        license=license_str,
        homepage=homepage,
    )
