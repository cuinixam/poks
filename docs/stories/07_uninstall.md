# Story 07 — Uninstall

## Goal

Implement the `Poks.uninstall()` method to remove installed apps from the `apps/` directory.

## Dependencies

- **Story 01** — Data Models & Config Parsing (for understanding the directory structure)

## Reference

- [specs.md — CLI Commands](../specs.md#cli-commands) (uninstall variants)

## Scope

### `Poks.uninstall()` Implementation

Replace the current stub in `src/poks/poks.py` with actual file deletion:

- **Uninstall specific version**: delete `apps/<name>/<version>/`. If the app directory is empty after removal, delete it too.
- **Uninstall all versions**: delete `apps/<name>/` entirely.
- **Uninstall all apps**: delete everything inside `apps/`.

### Error Handling

- Raise a descriptive error if the specified app/version does not exist.
- Log what was removed.

## Acceptance Criteria

- [x] Uninstalling a specific version removes only that version directory.
- [x] Uninstalling a specific version cleans up the parent directory if empty.
- [x] Uninstalling all versions removes the entire app directory.
- [x] Uninstalling all apps clears the apps directory.
- [x] Attempting to uninstall a non-existent app raises a clear error.
- [x] Tests use `tmp_path` with a pre-populated directory structure.
- [x] `pypeline run` passes.
