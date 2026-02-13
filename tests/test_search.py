"""Tests for the search command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from poks.main import app


@pytest.fixture
def runner() -> CliRunner:
    """Return a CliRunner instance."""
    return CliRunner()


@pytest.fixture
def mock_buckets_dir(tmp_path: Path) -> Path:
    """Create a mock buckets directory structure."""
    buckets_dir = tmp_path / "buckets"
    buckets_dir.mkdir()

    # Bucket 1
    bucket1 = buckets_dir / "bucket1"
    bucket1.mkdir()
    (bucket1 / "app-one.json").touch()
    (bucket1 / "app-two.json").touch()

    # Bucket 2
    bucket2 = buckets_dir / "bucket2"
    bucket2.mkdir()
    (bucket2 / "app-three.json").touch()
    (bucket2 / "another-app.json").touch()

    # Git bucket
    git_bucket = buckets_dir / "git-bucket"
    git_bucket.mkdir()
    (git_bucket / ".git").mkdir()
    (git_bucket / "git-app.json").touch()

    return buckets_dir


def test_search_finds_apps(runner: CliRunner, mock_buckets_dir: Path, tmp_path: Path) -> None:
    """Test searching for apps finds matches."""
    result = runner.invoke(app, ["search", "app", "--root", str(tmp_path), "--no-update"])

    assert result.exit_code == 0
    assert "Found 5 matching apps:" in result.stdout
    assert "another-app" in result.stdout
    assert "app-one" in result.stdout
    assert "app-two" in result.stdout
    assert "git-app" in result.stdout
    assert "app-three" in result.stdout


def test_search_case_insensitive(runner: CliRunner, mock_buckets_dir: Path, tmp_path: Path) -> None:
    """Test search is case insensitive."""
    # "ONE" should match "app-one"
    result = runner.invoke(app, ["search", "ONE", "--root", str(tmp_path), "--no-update"])

    assert result.exit_code == 0
    assert "Found 1 matching apps:" in result.stdout
    assert "app-one" in result.stdout


def test_search_no_matches(runner: CliRunner, mock_buckets_dir: Path, tmp_path: Path) -> None:
    """Test search with no matches."""
    result = runner.invoke(app, ["search", "nonexistent", "--root", str(tmp_path), "--no-update"])

    assert result.exit_code == 0
    assert "No apps found matching 'nonexistent'." in result.stdout


def test_search_updates_buckets(runner: CliRunner, mock_buckets_dir: Path, tmp_path: Path) -> None:
    """Test search updates buckets by default."""
    with patch("poks.bucket.Repo") as mock_repo:
        mock_repo_instance = MagicMock()
        mock_repo.return_value = mock_repo_instance

        result = runner.invoke(app, ["search", "app", "--root", str(tmp_path)])

        assert result.exit_code == 0
        # Should have tried to update git-bucket
        mock_repo.assert_called()
        mock_repo_instance.remotes.origin.fetch.assert_called()


def test_search_no_update_flag(runner: CliRunner, mock_buckets_dir: Path, tmp_path: Path) -> None:
    """Test --no-update flag skips update."""
    with patch("poks.bucket.Repo") as mock_repo:
        result = runner.invoke(app, ["search", "app", "--root", str(tmp_path), "--no-update"])

        assert result.exit_code == 0
        mock_repo.assert_not_called()
