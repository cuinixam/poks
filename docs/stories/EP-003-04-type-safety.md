# EP-003-04: Improve Type Safety

## Context

The codebase has good type hint coverage overall, but a few spots lose type information or suppress type/lint warnings in ways that contradict the project's own coding guidelines.

## Problems

### 1. `PoksJsonMixin.from_json_file` return type is too broad

`domain/models.py:21` — The classmethod returns `PoksJsonMixin` instead of `Self`. Callers like `PoksManifest.from_json_file(path)` lose the concrete type, requiring casts or ignoring type errors downstream.

```python
@classmethod
def from_json_file(cls, file_path: Path) -> PoksJsonMixin:  # Should be -> Self
```

### 2. `noqa` comments suppress legitimate warnings

The project's coding guidelines state: "Never suppress linter/type-checker warnings." Yet:

- `downloader.py:40` has `# noqa: S310`
- `extractor.py:55,57` has `# noqa: S202`

These should be addressed by fixing the underlying code (covered in EP-003-01) and then removing the `noqa` comments.

## Acceptance Criteria

- [ ] Change `from_json_file` return type to `Self` (using `typing.Self` for 3.11+ or `typing_extensions.Self` with conditional import for 3.10 compatibility).
- [ ] Verify all subclass usages of `from_json_file` benefit from the corrected return type.
- [ ] Remove `noqa` comments once the underlying code is fixed (depends on EP-003-01).
- [ ] All existing tests continue to pass.
- [ ] `pypeline run` passes with zero failures.

## Files to Modify

- `src/poks/domain/models.py`

## Dependencies

- `# noqa` removal depends on EP-003-01 being completed first.
