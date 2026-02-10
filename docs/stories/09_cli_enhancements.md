# Story 09 — CLI Enhancements

## Goal

Enhance the CLI to support single-app install from the command line (`poks install app@version --bucket name`) and polish error handling and user output.

## Dependencies

- **Story 06** — Install Orchestration
- **Story 07** — Uninstall

## Reference

- [specs.md — CLI Commands](../specs.md#cli-commands)

## Scope

### Single App Install

Extend the `install` command in `src/poks/main.py`:

- Support positional argument: `poks install zephyr-sdk@0.16.5-1`
- **`--bucket` (optional)** — narrows or provides the bucket:
  - If it looks like a URL (contains `://` or ends with `.git`), clone it on-the-fly and search there.
  - If it's a plain name, search only that local bucket (in `<root>/buckets/<name>`).
  - If omitted, search **all** locally available buckets for the manifest.
  - If no local buckets exist and no URL is given, fail with a clear error.
- This should create an in-memory `PoksConfig` and pass it directly to `Poks.install(config)` (see Story 06 — signature accepts `PoksConfig`).
- **No Persistence**: This command does **not** update `poks.json`. It performs a one-time install.
- Keep the existing `-c / --config` option for config-file-based install.
- Make the two modes mutually exclusive (error if both provided).

### User Output

- Print a summary of installed apps after `poks install`.
- Print what was removed after `poks uninstall`.
- Use clear error messages for common failures (missing config file, network error, unsupported platform).

### `--root` Default

- The `--root` option defaults to `~/.poks`. This is already in place — verify it works correctly with the full flow.

## Acceptance Criteria

- [ ] `poks install app@version` searches all local buckets and installs the app.
- [ ] `poks install app@version --bucket name` searches only the named local bucket.
- [ ] `poks install app@version --bucket <url>` clones the bucket and installs.
- [ ] No local buckets and no URL → clear error.
- [ ] `poks install -c poks.json` continues to work.
- [ ] Providing both `-c` and a positional argument produces an error.
- [ ] Install and uninstall commands print clear summaries.
- [ ] CLI tests cover all install modes and the uninstall variants.
- [ ] `pypeline run` passes.
