# EP-003-03: Code Quality Cleanup

## Context

The code review identified several code quality issues: dead code, duplicated logic, and missing error guards. None are critical bugs, but they reduce maintainability and violate the project's own coding guidelines.

## Problems

### 1. Dead code in `main.py` install command

`main.py:76-78` has an unreachable guard:

```python
if not app_spec:
    logger.error("Specify either -c/--config or app@version")
    raise typer.Exit(1)
```

This is unreachable because line 65 already exits when `app_spec` is falsy.

### 2. Duplicated git sync logic

`bucket.py` contains nearly identical git fetch+reset logic in both `sync_bucket` (lines 58-67) and `update_local_buckets` (lines 174-188). This should be extracted to a shared helper.

### 3. `bucket_paths` lookup raises raw `KeyError`

`poks.py:190` — `bucket_paths[app.bucket]` gives a raw `KeyError` when a bucket reference doesn't match. This should produce a descriptive `ValueError` instead.

### 4. `uninstall(all_apps=True)` crashes if `apps_dir` doesn't exist

`poks.py:331` — `self.apps_dir.iterdir()` raises `FileNotFoundError` when the directory hasn't been created yet. The `list_installed` method guards against this but `uninstall` does not.

### 5. Broad `except Exception` in `_resolve_installed_bucket`

`poks.py:286-287` catches bare `Exception`, masking potential programming errors. The `json.JSONDecodeError` catch above is sufficient for data issues.

### 6. Typo in project description

`pyproject.toml:4` — `"pre-build"` should be `"pre-built"`.

## Acceptance Criteria

- [ ] Remove the dead code block in `main.py:76-78`.
- [ ] Extract a `_pull_repo(repo_path)` helper in `bucket.py` used by both `sync_bucket` and `update_local_buckets`.
- [ ] Replace `bucket_paths[app.bucket]` with a `.get()` + descriptive `ValueError`.
- [ ] Guard `uninstall(all_apps=True)` against missing `apps_dir`.
- [ ] Remove or narrow the `except Exception` in `_resolve_installed_bucket`.
- [ ] Fix the typo in `pyproject.toml`.
- [ ] All existing tests continue to pass.

## Files to Modify

- `src/poks/main.py`
- `src/poks/bucket.py`
- `src/poks/poks.py`
- `pyproject.toml`
