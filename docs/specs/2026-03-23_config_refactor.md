# Config Refactor Specification

## Goal

Replace the deprecated `Config` class in `src/gh_tt/classes/config.py` with a modern, Pydantic-based config module at `src/gh_tt/modules/config.py`.

## Current State

The existing `Config` class:

- Lives in `src/gh_tt/classes/config.py` (deprecated area).
- Inherits from `Lazyload` (a legacy base class).
- Loads a bundled default `.tt-config.json` from `src/gh_tt/classes/`.
- Optionally deep-merges a user-supplied `.tt-config.json` from the git root.
- Supports JSON with line-comment stripping (`// ...`).
- Exposes config as a raw `dict` via `Config.config()`.
- Contains deprecated `.gitconfig` migration logic.
- Uses mutable class-level state (`ClassVar[dict]`, `ClassVar[list]`).

### Consumers (non-deprecated)

| File | Keys accessed |
|---|---|
| `workon.py` | `project.owner`, `project.number`, `workon.status` |
| `deliver.py` | (no direct access — receives `poll` as an arg) |
| `modules/tt_handlers.py` | `deliver.policies.poll` (modern path via `_resolve_poll_flag`) |

### Consumers (deprecated, in `classes/` — unchanged, keep using old `Config`)

| File | Keys accessed |
|---|---|
| `devbranch.py` | `squeeze.policies.*`, `wrapup.policies.warn_about_rebase`, `deliver.policies.branch_prefix` |
| `label.py` | `labels.*` |
| `project.py` | `project.owner`, `project.number` |
| `sync.py` | `sync.*` |
| `semver.py` | `semver.*` |

## Design

### Pydantic Models

Define a hierarchy of Pydantic `BaseModel` classes that mirrors the config JSON structure. All fields have defaults matching the current bundled `.tt-config.json`.

```python
from pydantic import BaseModel, ConfigDict

class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)

class ProjectConfig(FrozenModel):
    owner: str | None = None
    number: int | None = None

class WorkonConfig(FrozenModel):
    status: str = 'In Progress'

class DeliverPolicies(FrozenModel):
    poll: bool = False

class DeliverConfig(FrozenModel):
    status: str = 'Delivery Initiated'
    policies: DeliverPolicies = DeliverPolicies()

class TtConfig(FrozenModel):
    project: ProjectConfig = ProjectConfig()
    workon: WorkonConfig = WorkonConfig()
    deliver: DeliverConfig = DeliverConfig()
```

### Key design decisions

1. **Defaults live in the model, not in a JSON file.** The bundled `classes/.tt-config.json` is replaced by Pydantic field defaults. This eliminates file I/O, comment-stripping, and the `load_default_configuration` function.

2. **`project.owner` / `project.number` nullability.** Currently these default to empty strings and are later set to `None` if empty. The new model defaults them to `None` directly. The type of `number` becomes `int | None` (the old config stored it as a string, but all usage treats it as a number).

3. **No deprecated `.gitconfig` migration.** The `__assert_required` and `__set_required_from_gitconfig` methods are dropped entirely. They depend on `Lazyload` and `Gitter`, and are documented as deprecated.

4. **Only new-code-path config.** Models only cover keys consumed by the modern codebase (`workon.py`, `deliver.py`, `tt_handlers.py`). Legacy-only sections (`squeeze`, `wrapup`, `sync`, `semver`, `labels`, `workon.default_type_labels`, `deliver.policies.branch_prefix`) are omitted — deprecated callers in `classes/` continue using the old `Config` class.

### Module-level API

```python
# src/gh_tt/modules/config.py

CONFIG_FILE_NAME = '.tt-config.json'

def load_user_config(config_path: Path) -> dict:
    """Read a JSON file and return parsed dict.
    
    Raises:
        FileNotFoundError: if file does not exist.
        json.JSONDecodeError: if JSON is malformed.
    """
    ...

def load_config(git_root: Path | None = None) -> TtConfig:
    """Build config by layering user config on top of defaults.
    
    1. Start with Pydantic model defaults (no file needed).
    2. If git_root is provided and git_root / .tt-config.json exists,
       read it and merge via model_validate.
    3. Return the validated TtConfig instance.
    
    If git_root is None, returns defaults only.
    """
    ...
```

- **`load_config()` is a pure function.** It takes `git_root` as an explicit argument, has no global mutable state, and returns an immutable `TtConfig` object. This makes it trivially testable.
- Callers in the modern codebase (`workon.py`, `deliver.py`, `gh_tt.py`) call `load_config()` once at startup and thread the result through.
- Deprecated callers in `classes/` can continue using the old `Config` class — no changes to deprecated code.

### Merging strategy

The user file need only contain the keys they want to override. Pydantic handles this naturally:

```python
def load_config(git_root: Path | None = None) -> TtConfig:
    if git_root is None:
        return TtConfig()

    config_path = git_root / CONFIG_FILE_NAME
    if not config_path.exists():
        return TtConfig()

    user_data = load_user_config(config_path)
    return TtConfig.model_validate(user_data)
```

This preserves the deep-merge semantic: any key present in the user file overrides the default; absent keys keep their defaults.

### Error handling

- **Malformed JSON**: Catch json.JSONDecodeError and rethrow as a domain-specific exception ConfigParseError and let the exception bubble up to the caller.
- **Missing user config file**: Not an error — return defaults only.
- **Pydantic validation errors**: Catch `ValidationError` and rethrow as domain-specific ConfigValidationError and propagate to the caller. This is a new, stricter behavior that catches misconfiguration early rather than silently ignoring bad values.

## Migration Path

### Phase 1: New module (this work)

- Implement `src/gh_tt/modules/config.py` with models and `load_config()`.
- Add tests in `tests/test_config_module.py`.
- Do **not** modify any deprecated code in `classes/`.

### Phase 2: Wire into modern code

- In `gh_tt.py`, call `load_config(git_root)` at startup.
- Pass the `TtConfig` instance to `workon.py` and `tt_handlers.py` as a function argument.
- Update `workon.py` to use typed attribute access (`config.workon.status`) instead of dict access (`config['workon']['status']`).
- Update `tt_handlers.py` similarly.

### Phase 3: Deprecation cleanup (out of scope)

- When all `classes/` consumers are retired, remove `classes/config.py`, `classes/.tt-config.json`, and `classes/lazyload.py`.

## Testing

Tests go in `tests/test_config_module.py`. Cover:

1. **Defaults** — `TtConfig()` produces the expected default values for every field.
2. **User override** — `load_config()` with a user file merges correctly (partial overrides keep defaults).
3. **Malformed JSON** — `load_config()` exits with code 1 and prints to stderr.
4. **Missing user file** — `load_config()` returns defaults without error.
5. **Validation errors** — Invalid types (e.g. `number: "abc"`) raise `ValidationError`.
6. **Unknown keys ignored** — User JSON with keys not in the model (e.g. `squeeze`, `labels`) is silently ignored.

## Resolved Questions

1. **Should `load_config()` discover `git_root` itself?** No — it takes `git_root` as a parameter for testability. The caller (`gh_tt.py`) already has access to `git_root` via `Gitter.git_root` or `git.get_root()`.

2. **Frozen models?** Yes. All models inherit from a shared `FrozenModel` base with `ConfigDict(frozen=True)`. Pydantic's `frozen` does not propagate to nested models automatically, so the shared base class ensures immutability at every level.
