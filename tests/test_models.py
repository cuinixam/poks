import json

import pytest

from poks.domain import PoksApp, PoksBucket, PoksConfig, PoksManifest

SAMPLE_MANIFEST = {
    "version": "0.16.5-1",
    "description": "Zephyr SDK Bundle",
    "homepage": "https://github.com/zephyrproject-rtos/sdk-ng",
    "license": "Apache-2.0",
    "url": "https://example.com/sdk-${version}_${os}-${arch}${ext}",
    "archives": [
        {"os": "windows", "arch": "x86_64", "ext": ".7z", "sha256": "abc123"},
        {"os": "linux", "arch": "x86_64", "sha256": "def456", "url": "https://mirror.example.com/sdk-linux.tar.xz"},
    ],
    "extract_dir": "zephyr-sdk-0.16.5-1",
    "bin": ["bin"],
    "env": {"ZEPHYR_SDK_INSTALL_DIR": "${dir}"},
}

MINIMAL_MANIFEST = {
    "version": "1.0.0",
    "archives": [{"os": "linux", "arch": "x86_64", "sha256": "aaa"}],
}

SAMPLE_CONFIG = {
    "buckets": [
        {"name": "main", "url": "https://github.com/poks/main-bucket.git"},
        {"name": "extras", "url": "https://github.com/poks/extras-bucket.git"},
    ],
    "apps": [
        {"name": "cmake", "version": "3.28.1", "bucket": "main"},
        {"name": "mingw-libs", "version": "1.0.0", "bucket": "extras", "os": ["windows"]},
    ],
}


class TestPoksManifest:
    def test_from_json_file_full(self, tmp_path):
        path = tmp_path / "manifest.json"
        path.write_text(json.dumps(SAMPLE_MANIFEST))
        manifest = PoksManifest.from_json_file(path)

        assert manifest.version == "0.16.5-1"
        assert manifest.description == "Zephyr SDK Bundle"
        assert manifest.license == "Apache-2.0"
        assert len(manifest.archives) == 2
        assert manifest.archives[0].os == "windows"
        assert manifest.archives[1].url == "https://mirror.example.com/sdk-linux.tar.xz"
        assert manifest.bin == ["bin"]
        assert manifest.env == {"ZEPHYR_SDK_INSTALL_DIR": "${dir}"}

    def test_from_json_file_minimal(self, tmp_path):
        path = tmp_path / "manifest.json"
        path.write_text(json.dumps(MINIMAL_MANIFEST))
        manifest = PoksManifest.from_json_file(path)

        assert manifest.version == "1.0.0"
        assert manifest.description is None
        assert manifest.url is None
        assert manifest.bin is None
        assert manifest.env is None

    def test_round_trip(self, tmp_path):
        path = tmp_path / "manifest.json"
        path.write_text(json.dumps(SAMPLE_MANIFEST))
        original = PoksManifest.from_json_file(path)

        out_path = tmp_path / "out.json"
        original.to_json_file(out_path)
        reloaded = PoksManifest.from_json_file(out_path)

        assert original == reloaded

    def test_round_trip_omits_none(self, tmp_path):
        path = tmp_path / "manifest.json"
        path.write_text(json.dumps(MINIMAL_MANIFEST))
        manifest = PoksManifest.from_json_file(path)

        out_path = tmp_path / "out.json"
        manifest.to_json_file(out_path)
        raw = json.loads(out_path.read_text())

        assert "description" not in raw
        assert "homepage" not in raw
        assert "bin" not in raw


class TestPoksConfig:
    def test_from_json_file(self, tmp_path):
        path = tmp_path / "poks.json"
        path.write_text(json.dumps(SAMPLE_CONFIG))
        config = PoksConfig.from_json_file(path)

        assert len(config.buckets) == 2
        assert config.buckets[0] == PoksBucket(name="main", url="https://github.com/poks/main-bucket.git")
        assert len(config.apps) == 2
        assert config.apps[0].name == "cmake"
        assert config.apps[1].os == ["windows"]

    def test_round_trip(self, tmp_path):
        path = tmp_path / "poks.json"
        path.write_text(json.dumps(SAMPLE_CONFIG))
        original = PoksConfig.from_json_file(path)

        out_path = tmp_path / "out.json"
        original.to_json_file(out_path)
        reloaded = PoksConfig.from_json_file(out_path)

        assert original == reloaded


@pytest.mark.parametrize(
    ("os_filter", "arch_filter", "query_os", "query_arch", "expected"),
    [
        (None, None, "linux", "x86_64", True),
        (["windows"], None, "windows", "x86_64", True),
        (["windows"], None, "linux", "x86_64", False),
        (None, ["aarch64"], "macos", "aarch64", True),
        (None, ["aarch64"], "macos", "x86_64", False),
        (["linux", "macos"], ["x86_64"], "linux", "x86_64", True),
        (["linux", "macos"], ["x86_64"], "windows", "x86_64", False),
        (["linux"], ["aarch64"], "linux", "x86_64", False),
    ],
)
def test_is_supported(os_filter, arch_filter, query_os, query_arch, expected):
    app = PoksApp(name="tool", version="1.0", bucket="main", os=os_filter, arch=arch_filter)
    assert app.is_supported(query_os, query_arch) is expected


def test_invalid_json(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("not valid json")
    with pytest.raises(json.JSONDecodeError):
        PoksConfig.from_json_file(path)
