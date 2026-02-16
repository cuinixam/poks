"""Tests for Scoop manifest to Poks manifest conversion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from poks.scoop import convert_scoop_manifest


def _write_scoop_manifest(tmp_path: Path, data: dict[str, Any]) -> Path:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(data))
    return manifest


class TestConvertScoopManifest:
    def test_architecture_based_manifest(self, tmp_path: Path) -> None:
        scoop = {
            "version": "14.2.0",
            "description": "GCC compiler",
            "homepage": "https://example.com",
            "license": "GPL-3.0",
            "architecture": {
                "64bit": {
                    "url": "https://example.com/gcc-14.2.0-x64.7z",
                    "hash": "abc123",
                    "extract_dir": "mingw64",
                },
                "32bit": {
                    "url": "https://example.com/gcc-14.2.0-x86.7z",
                    "hash": "def456",
                    "extract_dir": "mingw32",
                },
            },
            "env_add_path": "bin",
        }
        result = convert_scoop_manifest(_write_scoop_manifest(tmp_path, scoop))

        assert result.description == "GCC compiler"
        assert result.homepage == "https://example.com"
        assert result.license == "GPL-3.0"
        assert len(result.versions) == 1

        version = result.versions[0]
        assert version.version == "14.2.0"
        assert version.bin_dirs == ["bin"]
        assert len(version.archives) == 2

        x64 = version.archives[0]
        assert x64.os == "windows"
        assert x64.arch == "x86_64"
        assert x64.sha256 == "abc123"
        assert x64.ext == ".7z"
        assert x64.extract_dir == "mingw64"

        x86 = version.archives[1]
        assert x86.os == "windows"
        assert x86.arch == "x86"
        assert x86.sha256 == "def456"
        assert x86.extract_dir == "mingw32"

    def test_toplevel_url_manifest(self, tmp_path: Path) -> None:
        scoop = {
            "version": "1.0.0",
            "description": "Simple tool",
            "url": "https://example.com/tool-1.0.0.zip",
            "hash": "aaa111",
        }
        result = convert_scoop_manifest(_write_scoop_manifest(tmp_path, scoop))

        assert len(result.versions[0].archives) == 1
        archive = result.versions[0].archives[0]
        assert archive.os == "windows"
        assert archive.arch == "x86_64"
        assert archive.url == "https://example.com/tool-1.0.0.zip"
        assert archive.sha256 == "aaa111"
        assert archive.ext == ".zip"

    def test_license_as_object(self, tmp_path: Path) -> None:
        scoop = {
            "version": "1.0.0",
            "description": "Licensed tool",
            "license": {"identifier": "MIT", "url": "https://example.com/license"},
            "url": "https://example.com/tool.zip",
            "hash": "bbb222",
        }
        result = convert_scoop_manifest(_write_scoop_manifest(tmp_path, scoop))
        assert result.license == "MIT"

    def test_env_set_mapping(self, tmp_path: Path) -> None:
        scoop = {
            "version": "1.0.0",
            "description": "Tool with env",
            "url": "https://example.com/tool.tar.gz",
            "hash": "ccc333",
            "env_set": {"MY_VAR": "my_value", "OTHER": "other_value"},
        }
        result = convert_scoop_manifest(_write_scoop_manifest(tmp_path, scoop))
        assert result.versions[0].env == {"MY_VAR": "my_value", "OTHER": "other_value"}

    def test_bin_field_extracts_dirs(self, tmp_path: Path) -> None:
        scoop = {
            "version": "1.0.0",
            "description": "Tool with bin",
            "url": "https://example.com/tool.zip",
            "hash": "ddd444",
            "bin": ["tools/bin/gcc.exe", "tools/bin/g++.exe", "lib/ld.exe"],
        }
        result = convert_scoop_manifest(_write_scoop_manifest(tmp_path, scoop))
        assert result.versions[0].bin_dirs == ["tools/bin", "lib"]

    def test_compound_extension(self, tmp_path: Path) -> None:
        scoop = {
            "version": "1.0.0",
            "description": "Tarball tool",
            "url": "https://example.com/tool-1.0.0.tar.gz",
            "hash": "eee555",
        }
        result = convert_scoop_manifest(_write_scoop_manifest(tmp_path, scoop))
        assert result.versions[0].archives[0].ext == ".tar.gz"

    def test_unconvertible_fields_ignored(self, tmp_path: Path) -> None:
        """Unconvertible scoop fields like post_install are silently skipped."""
        scoop = {
            "version": "1.0.0",
            "description": "Tool with scripts",
            "url": "https://example.com/tool.zip",
            "hash": "fff666",
            "post_install": "echo done",
            "shortcuts": [["tool.exe", "Tool"]],
        }
        result = convert_scoop_manifest(_write_scoop_manifest(tmp_path, scoop))
        # Conversion succeeds despite unconvertible fields
        assert result.description == "Tool with scripts"
        assert len(result.versions[0].archives) == 1

    def test_shared_extract_dir_at_version_level(self, tmp_path: Path) -> None:
        """When all arches share the same extract_dir, it goes to version level only."""
        scoop = {
            "version": "1.0.0",
            "description": "Tool",
            "extract_dir": "inner",
            "architecture": {
                "64bit": {"url": "https://example.com/x64.7z", "hash": "a1"},
                "32bit": {"url": "https://example.com/x86.7z", "hash": "b2"},
            },
        }
        result = convert_scoop_manifest(_write_scoop_manifest(tmp_path, scoop))
        assert result.versions[0].extract_dir == "inner"
        # Archives should NOT duplicate the version-level extract_dir
        assert result.versions[0].archives[0].extract_dir is None
        assert result.versions[0].archives[1].extract_dir is None

    def test_url_as_list(self, tmp_path: Path) -> None:
        scoop = {
            "version": "1.0.0",
            "description": "Multi-URL tool",
            "url": ["https://example.com/main.zip", "https://example.com/extra.zip"],
            "hash": ["aaa111", "bbb222"],
        }
        result = convert_scoop_manifest(_write_scoop_manifest(tmp_path, scoop))
        # Only first URL is used
        assert result.versions[0].archives[0].url == "https://example.com/main.zip"
        assert result.versions[0].archives[0].sha256 == "aaa111"

    def test_roundtrip_serialization(self, tmp_path: Path) -> None:
        scoop = {
            "version": "2.0.0",
            "description": "Roundtrip test",
            "homepage": "https://example.com",
            "license": "Apache-2.0",
            "url": "https://example.com/tool-2.0.0.zip",
            "hash": "abc123",
            "env_add_path": "bin",
        }
        result = convert_scoop_manifest(_write_scoop_manifest(tmp_path, scoop))
        output = tmp_path / "output.json"
        result.to_json_file(output)

        loaded = json.loads(output.read_text())
        assert loaded["description"] == "Roundtrip test"
        assert loaded["versions"][0]["version"] == "2.0.0"
        assert loaded["versions"][0]["bin_dirs"] == ["bin"]
