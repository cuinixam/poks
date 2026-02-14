# EP-003-01: Security Hardening for Downloads and Extraction

## Context

Poks downloads archives from URLs specified in manifests and extracts them to the local filesystem. Several security risks exist in the current implementation that could be exploited by malicious manifests.

## Problems

### 1. `urlretrieve` has no timeout and follows redirects silently

`downloader.py:40` uses `urlretrieve` with a `# noqa: S310` to suppress Bandit's warning. This function:

- Has no timeout — a slow server can hang the process indefinitely.
- Follows HTTP redirects without limit — a malicious URL could redirect to internal network addresses (SSRF).
- Provides no control over TLS verification or redirect policy.

### 2. `extract_dir` path traversal in `_relocate_extract_dir`

`extractor.py:66-71` takes `extract_dir` from the manifest JSON without validation. A value like `../../etc` would cause `shutil.move` to write files outside the intended installation directory.

### 3. Zip extraction lacks path traversal protection

`extractor.py:54-61` — Tar extraction uses `filter="data"` on Python 3.12+ (good), but the fallback on older Pythons and all zip extractions have no path traversal protection. A crafted zip with entries like `../../../etc/passwd` could write files outside the destination.

## Acceptance Criteria

- [x] Replace `urlretrieve` with `urllib.request.urlopen` (or equivalent) with an explicit timeout (e.g., 60s).
- [x] Validate `extract_dir` stays within `dest_dir` using `Path.resolve().is_relative_to()`.
- [x] Validate zip entry names before extraction to prevent path traversal (reject entries containing `..`).
- [x] For tar on Python < 3.12, add manual path validation for each member.
- [x] Remove all `# noqa: S310` and `# noqa: S202` comments — fix the underlying code instead.
- [x] All existing tests continue to pass.
- [x] Add tests for path traversal attempts (zip and extract_dir).

## Files to Modify

- `src/poks/downloader.py`
- `src/poks/extractor.py`
- `tests/test_downloader.py`
- `tests/test_extractor.py`
