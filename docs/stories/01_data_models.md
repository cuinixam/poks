# Story 01 — Data Models & Config Parsing

## Goal

Define the core dataclasses for the Poks domain and implement JSON deserialization for both **manifest files** and the **configuration file** (`poks.json`).

## Dependencies

None — this is a foundational story.

## Reference

- [specs.md — Manifest Schema](../specs.md#manifest-schema)
- [specs.md — Configuration File](../specs.md#2-configuration-file-poksjson)

## Mashumaro Pattern

Use the same `DataClassJSONMixin` pattern as the existing `ScoopInstall` step in `pypeline`. Each dataclass should:

1. Inherit from `DataClassJSONMixin` (from `mashumaro.mixins.json`).
2. Include a `Config(BaseConfig)` inner class with `TO_DICT_ADD_OMIT_NONE_FLAG` so `None` fields are omitted during serialization.
3. Provide `from_json_file(cls, path) -> Self` and `to_json_file(self, path) -> None` helper methods for file I/O.

```python
from dataclasses import dataclass
from mashumaro.config import TO_DICT_ADD_OMIT_NONE_FLAG, BaseConfig
from mashumaro.mixins.json import DataClassJSONMixin

@dataclass
class PoksManifest(DataClassJSONMixin):
    version: str
    archives: list[PoksArchive]
    # ... optional fields ...

    class Config(BaseConfig):
        code_generation_options = [TO_DICT_ADD_OMIT_NONE_FLAG]

    @classmethod
    def from_json_file(cls, file_path: Path) -> "PoksManifest":
        return cls.from_dict(json.loads(file_path.read_text()))

    def to_json_file(self, file_path: Path) -> None:
        file_path.write_text(json.dumps(self.to_dict(omit_none=True), indent=2))
```

Avoid duplicating the `Config` and file I/O logic — extract a base mixin or use a shared helper if the pattern repeats across multiple dataclasses.

## Scope

### Data Models

Create a new module `src/poks/models.py` with the following dataclasses:

| Dataclass | Fields |
|-----------|--------|
| `PoksArchive` | `os: str`, `arch: str`, `sha256: str`, `ext: Optional[str]`, `url: Optional[str]` |
| `PoksManifest` | `version: str`, `description: Optional[str]`, `homepage: Optional[str]`, `license: Optional[str]`, `url: Optional[str]`, `archives: list[PoksArchive]`, `extract_dir: Optional[str]`, `bin: Optional[list[str]]`, `env: Optional[dict[str, str]]` |
| `PoksBucket` | `name: str`, `url: str` |
| `PoksApp` | `name: str`, `version: str`, `bucket: str`, `os: Optional[list[str]]`, `arch: Optional[list[str]]` |
| `PoksConfig` | `buckets: list[PoksBucket]`, `apps: list[PoksApp]` |

### Parsing

`from_json_file` class methods on `PoksConfig` and `PoksManifest` replace the need for standalone parse functions — the dataclass itself knows how to deserialize from a file path.

### Platform Filtering

- `PoksApp` should expose a helper `is_supported(os: str, arch: str) -> bool` that returns `True` when the app's `os`/`arch` filters match (or are `None`, meaning all platforms).
- **Convention**: The `os` and `arch` values use Poks conventions (`windows`, `linux`, `macos`, `x86_64`, `aarch64`), not raw `platform` module values. Callers must map values before calling this method (see Story 06 — `get_current_platform()`).

## Acceptance Criteria

- [x] All dataclasses use `DataClassJSONMixin` with `BaseConfig` and `omit_none = True`.
- [x] `PoksConfig.from_json_file` correctly loads a sample `poks.json`.
- [x] `PoksManifest.from_json_file` correctly loads a sample manifest JSON.
- [x] `to_json_file` round-trips correctly (omitting `None` fields).
- [x] `is_supported` filters apps by OS and architecture.
- [x] Parametrized pytest tests cover valid input, missing optional fields, and invalid JSON.
- [x] `pypeline run` passes.
