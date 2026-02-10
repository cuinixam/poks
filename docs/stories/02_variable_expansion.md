# Story 02 — Variable Expansion & Archive Resolution

## Goal

Implement the manifest variable expansion system (`${version}`, `${os}`, `${arch}`, `${ext}`, `${dir}`) and the logic to resolve which archive entry matches the current platform.

## Dependencies

- **Story 01** — Data Models & Config Parsing (uses `PoksManifest`, `PoksArchive`)

## Reference

- [specs.md — URL Resolution](../specs.md#url-resolution)
- [specs.md — Variable Expansion](../specs.md#variable-expansion)
- [specs.md — Supported Platforms](../specs.md#supported-platforms)

## Scope

### Variable Expansion

Create a function (or utility module `src/poks/resolver.py`):

- `expand_variables(template: str, variables: dict[str, str]) -> str` — replaces `${key}` placeholders in a template string with values from the variables dict.

### Archive Resolution

- `resolve_archive(manifest: PoksManifest, target_os: str, target_arch: str) -> PoksArchive` — iterates through `manifest.archives` and returns the first match for `(target_os, target_arch)`. Raises a descriptive error if no match is found.

### URL Resolution

- `resolve_download_url(manifest: PoksManifest, archive: PoksArchive) -> str` — if the archive has a `url`, return it (with variables expanded). Otherwise, expand the manifest's root `url` template using the archive's fields plus `version`.

## Acceptance Criteria

- [ ] Variable expansion replaces all supported placeholders.
- [ ] Unknown variables are left as-is (no crash).
- [ ] `resolve_archive` returns the correct entry for a given OS/arch pair.
- [ ] `resolve_archive` raises a clear error for unsupported platforms.
- [ ] `resolve_download_url` uses the archive URL when present, falls back to the manifest template.
- [ ] Parametrized tests cover multiple OS/arch combinations and missing templates.
- [ ] `pypeline run` passes.
