"""Unit tests for the list command and API."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from poks.domain import PoksAppVersion, PoksManifest
from poks.main import app
from tests.conftest import PoksEnv
from tests.helpers import assert_installed_app

runner = CliRunner()


def test_list_api_returns_installed_apps(poks_env: PoksEnv, tmp_path: Path) -> None:
    """Test that poks.list_installed() returns installed apps with details."""
    app_name = "test-app"
    version = "1.0.0"
    install_dir = poks_env.apps_dir / app_name / version
    install_dir.mkdir(parents=True)

    manifest = PoksManifest(description="Test App", versions=[PoksAppVersion(version=version, archives=[], bin_dirs=["bin"], env={"MY_VAR": "${dir}/data"})])
    (install_dir / ".manifest.json").write_text(manifest.to_json_string())

    (install_dir / "bin").mkdir()

    result = poks_env.poks.list_installed()

    installed = assert_installed_app(result, app_name)
    assert installed.version == version
    assert installed.install_dir == install_dir
    assert installed.bin_dirs == [install_dir / "bin"]
    assert installed.env["MY_VAR"] == str(install_dir / "data")

    # Aggregated helpers
    assert result.dirs == [install_dir / "bin"]
    assert result.env == {"MY_VAR": str(install_dir / "data")}


def test_cli_list_command(poks_env: PoksEnv) -> None:
    """Test that 'poks list' prints the table of apps."""
    app_name = "cli-app"
    version = "2.0.0"
    install_dir = poks_env.apps_dir / app_name / version
    install_dir.mkdir(parents=True)

    manifest = PoksManifest(description="CLI App", versions=[PoksAppVersion(version=version, archives=[])])
    (install_dir / ".manifest.json").write_text(manifest.to_json_string())

    result = runner.invoke(app, ["list", "--root", str(poks_env.root_dir)])

    assert result.exit_code == 0
    assert "Name" in result.stdout
    assert "Version" in result.stdout
    assert app_name in result.stdout
    assert version in result.stdout


def test_list_empty(poks_env: PoksEnv) -> None:
    """Test list command with no apps installed."""
    result = runner.invoke(app, ["list", "--root", str(poks_env.root_dir)])
    assert result.exit_code == 0
    assert "No apps installed." in result.stdout
