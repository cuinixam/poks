"""Bucket syncing and manifest lookup."""

from pathlib import Path

from git import Repo
from py_app_dev.core.logging import logger

from poks.domain import PoksBucket


def sync_bucket(bucket: PoksBucket, buckets_dir: Path) -> Path:
    """Clone or pull a bucket repository and return its local path."""
    local_path = buckets_dir / bucket.name
    if local_path.exists():
        logger.info(f"Pulling latest for bucket '{bucket.name}'")
        repo = Repo(local_path)
        repo.remotes.origin.fetch()
        repo.head.reset(repo.active_branch.tracking_branch(), index=True, working_tree=True)
    else:
        logger.info(f"Cloning bucket '{bucket.name}' from {bucket.url}")
        Repo.clone_from(bucket.url, str(local_path))
    return local_path


def find_manifest(app_name: str, bucket_path: Path) -> Path:
    """Return the path to ``<app_name>.json`` inside the bucket directory."""
    manifest_path = bucket_path / f"{app_name}.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest '{app_name}.json' not found in bucket at {bucket_path}")
    return manifest_path


def sync_all_buckets(buckets: list[PoksBucket], buckets_dir: Path) -> dict[str, Path]:
    """Sync every bucket and return a ``{name: local_path}`` mapping."""
    return {bucket.name: sync_bucket(bucket, buckets_dir) for bucket in buckets}


def is_bucket_url(value: str) -> bool:
    """Check if a string looks like a bucket URL (contains :// or ends with .git)."""
    return "://" in value or value.endswith(".git")


def search_all_buckets(app_name: str, buckets_dir: Path) -> tuple[Path, str]:
    """
    Search all local buckets for a manifest and return its path and bucket name.

    Args:
        app_name: Name of the app to search for.
        buckets_dir: Directory containing local buckets.

    Returns:
        Tuple of (manifest_path, bucket_name).

    Raises:
        FileNotFoundError: If no buckets exist or manifest not found in any bucket.

    """
    if not buckets_dir.exists() or not any(buckets_dir.iterdir()):
        raise FileNotFoundError("No local buckets available. Use --bucket with a URL to clone a bucket.")

    for bucket_dir in buckets_dir.iterdir():
        if not bucket_dir.is_dir():
            continue
        manifest_path = bucket_dir / f"{app_name}.json"
        if manifest_path.exists():
            return manifest_path, bucket_dir.name

    raise FileNotFoundError(f"Manifest '{app_name}.json' not found in any local bucket")


def search_apps_in_buckets(query: str, buckets_dir: Path) -> list[str]:
    """
    Search for apps in all local buckets matching the query.

    Args:
        query: Search term (case-insensitive substring).
        buckets_dir: Directory containing local buckets.

    Returns:
        Sorted list of matching app names.

    """
    matches = set()
    if not buckets_dir.exists():
        return []

    query = query.lower()

    for bucket_dir in buckets_dir.iterdir():
        if not bucket_dir.is_dir():
            continue

        for item in bucket_dir.iterdir():
            if item.suffix == ".json" and item.is_file():
                app_name = item.stem
                if query in app_name.lower():
                    matches.add(app_name)

    return sorted(matches)


def update_local_buckets(buckets_dir: Path) -> None:
    """
    Update all local buckets that are git repositories.

    Args:
        buckets_dir: Directory containing local buckets.

    """
    if not buckets_dir.exists():
        return

    for bucket_dir in buckets_dir.iterdir():
        if not bucket_dir.is_dir():
            continue

        # Check if it's a git repo
        if (bucket_dir / ".git").exists():
            try:
                logger.info(f"Updating bucket '{bucket_dir.name}'...")
                repo = Repo(bucket_dir)
                repo.remotes.origin.fetch()
                repo.head.reset(repo.active_branch.tracking_branch(), index=True, working_tree=True)
            except Exception as e:
                logger.warning(f"Failed to update bucket '{bucket_dir.name}': {e}")
