# Semver Testing Improvement Spec

**Date**: 2026-03-23
**Goal**: Achieve comprehensive boundary-level test coverage for the semver subsystem before refactoring, to guarantee no breaking changes.

## Guiding principle

**No mocking.** The semver subsystem has very few external dependencies — all of them are git commands. Instead of mocking `Gitter` or `git.*`, we set up temporary git repositories as fixtures and run real commands against them. This gives us high confidence that the refactored code actually works.

The only things that genuinely cannot be tested without mocking are calls to GitHub's API — none of the semver code paths use `gh`, so this doesn't apply here.

## Current state

### Coverage
- `semver.py`: **81%** (283 stmts, 53 missed) — the missed lines are mostly in `bump` (live mode), `note_md`, and `_determine_from_ref`.
- `tt_handlers.py`: **29%** — the `handle_semver` / `_handle_semver_bump` / `_handle_semver_bump_build` paths are entirely untested.

### What exists today

| File | What it covers | Approach |
|---|---|---|
| `test_semver.py` | `SemverVersion` bumps (hypothesis), `from_string` roundtrip, `_parse_tags` (hypothesis), `_get_next_semvers` (hypothesis), `Semver.list`, `get_current_semver`, `bump` (dry-run), invalid parsing, prefix handling, `bump_build` (no SHA) | Mix of direct construction and JSON fixtures loaded via `from_json` |
| `test_semver_prerelease.py` | `SemverVersion.__lt__` for prerelease and build comparisons | Small manual test set |
| `test_semver_list_sha.py` | `list(show_sha=True/False)`, `SemverTag` with SHA | Uses `MagicMock` for `semver.get` |
| `test_semver_note_with_from_to.py` | `note()` with explicit and default `from_ref`/`to_ref` | Fully mocked — doesn't validate actual output |
| `test_parser_semver_*.py` (3 files) | CLI parser flags | Direct — good as-is |
| `test_handlers.py` | `handle_workon`/`handle_deliver` legacy abort only | No `handle_semver` tests |

### Test data
Five JSON fixtures in `tests/data/semver/`. These are used to hydrate `Semver` instances via `from_json` and bypass git entirely. This approach has value for pure parsing logic, but it skips the real integration path (`with_tags_loaded` → git commands → `_parse_tags`).

## Gap analysis

### 1. `SemverVersion` — pure logic, no git needed

These are already well-tested. Gaps:

- **Roundtrip with build metadata**: The hypothesis `semver_versions` strategy never generates `build`, so `from_string`/`__str__` roundtrip is untested for versions like `1.0.0+build.42`.
- **`bump_prerelease` branch coverage**: Missing tests for prerelease with no trailing number (`"alpha"` → `"alpha1"`), purely numeric prerelease (`"42"` → `"43"` via dot-split path), and dot-separated numeric tail (`"alpha.3"` → `"alpha.4"`).
- **`bump_build` with SHA**: The `include_sha=True` path calls `git.get_branch_tip_hash` — needs a real git repo, not a mock.
- **Comparison edge cases**: Equal versions returning `False` for `__lt__` (sort stability), transitivity, antisymmetry — only partially covered by the handful of manual tests in `test_semver_prerelease.py`.

### 2. `SemverTag` — pure logic, no git needed

- `from_string` happy path (with/without prefix, with/without SHA) — only exercised indirectly through `_parse_tags`.
- `from_string` returning `None` for invalid input — not tested.
- `__lt__` delegation to `SemverVersion.__lt__` — not directly tested.

### 3. `Semver` orchestration — currently uses JSON fixtures or mocks

- **`_parse_tags`**: Tested with hypothesis (tag count preservation), but never with prefixed tags, build metadata tags, or the `tag_shas_string` parameter used directly.
- **`_get_next_semvers`**: Called via hypothesis but no assertions on returned values. The `current_prerelease=None` path (prerelease nexts derived from release) is untested.
- **`get_current_semver`**: Works. Missing: empty tag list → `None`.
- **`bump` (live mode)**: Completely untested — this actually creates a git tag. Should be tested in a real repo.
- **`list`**: Only `filter_type='all'` tested (via SHA test with mocks). Individual filters, sort order, backwards-compat coercion — all untested.
### 4. `handle_semver` — completely untested

All dispatch logic (no-subcommand, bump, list) and the `_handle_semver_bump_build` error path.

## Testing approach

### Temporary git repo fixture

A `pytest` fixture that creates a real git repository in `tmp_path`. Tests that need tags, commits, or SHA information use this fixture instead of JSON files or mocks.

```python
@pytest.fixture
async def semver_repo(tmp_path, monkeypatch):
    """Create a temporary git repo with commits and tags for semver testing.

    Returns a helper object that can create commits and tags on demand.
    Uses shell.run() for all git operations, consistent with the rest of the codebase.
    """
    monkeypatch.chdir(tmp_path)
    # Gitter.workdir is a class variable that defaults to Path.cwd()
    # at import time. Override it so Gitter commands run in our temp repo.
    monkeypatch.setattr(Gitter, 'workdir', tmp_path)

    await shell.run(['git', 'init'], cwd=tmp_path)
    await shell.run(['git', 'config', 'user.email', 'test@test.com'], cwd=tmp_path)
    await shell.run(['git', 'config', 'user.name', 'Test'], cwd=tmp_path)

    class RepoHelper:
        def __init__(self):
            self.path = tmp_path

        async def commit(self, message='test commit'):
            await shell.run(
                ['git', 'commit', '--allow-empty', '-m', message],
                cwd=tmp_path,
            )

        async def tag(self, name, message=None):
            cmd = ['git', 'tag']
            if message:
                cmd += ['-a', '-m', message]
            cmd.append(name)
            await shell.run(cmd, cwd=tmp_path)

        async def get_head_sha(self):
            result = await shell.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=tmp_path,
            )
            return result.stdout

    return RepoHelper()
```

Since `Gitter.fetch()` (called by `_load_manifest`) runs `git fetch --tags --all` which requires a remote, tests that use `Semver.with_tags_loaded()` will need to also disable the fetch. The cleanest approach is to set `Gitter.fetched = True` in the fixture via `monkeypatch`, which skips the fetch call entirely — this is a single class-level flag, not a mock of behaviour.

> Note: `Gitter.fetched` is a class-level boolean flag that `Gitter.fetch()` checks before attempting to fetch. Setting it to `True` causes the fetch to be skipped. This is the production skip mechanism, not a mock. If `Gitter.fetch` does not have this guard yet, the fixture should `monkeypatch` `Gitter.fetch` to a no-op coroutine — this is the one acceptable concession since `fetch` is a network operation and the temp repo has no remote.

### What stays as-is

- **Parser tests** (`test_parser_semver_*.py`): Already good. No git needed for argparse testing.
- **`SemverVersion` pure logic tests** in `test_semver.py`: Direct construction, hypothesis strategies — these are perfect as-is and just need gap-filling.
- **`test_semver_prerelease.py`**: Direct construction comparisons — fine as-is, extend with more cases.

### What changes

- **`test_semver_list_sha.py`**: Replace `MagicMock` approach with the `semver_repo` fixture. Create real tags, call `Semver.with_tags_loaded()` or `Semver(tag_string=...)`, verify output.

### Out of scope

- **`note` / `note_md` / `_determine_from_ref`**: The `note` command may be removed soon. No new tests for these paths.

## Proposed new tests

### A. `SemverVersion` pure logic — extend `test_semver.py` (no git needed)

| Test | Technique |
|---|---|
| `test_semver_version_parse_roundtrip_with_build` | Extend hypothesis `semver_versions` strategy to optionally generate `build` |
| `test_bump_prerelease_no_trailing_number` | `SemverVersion(1,0,0,"alpha").bump_prerelease()` → `"alpha1"` |
| `test_bump_prerelease_purely_numeric` | `SemverVersion(1,0,0,None,"42")` — verify dot-split path |
| `test_bump_prerelease_dot_separated` | `SemverVersion(1,0,0,"alpha.3").bump_prerelease()` → `"alpha.4"` |
| `test_equal_versions_not_less_than` | Parametrize: plain, with prerelease, with build, with both — assert `not (v < v)` |
| `test_comparison_transitivity` | Hypothesis: if `a < b` and `b < c` then `a < c` |
| `test_comparison_antisymmetry` | Hypothesis: if `a < b` then `not (b < a)` |
| `test_is_prerelease` | Parametrize: `True` when prerelease is set, `False` otherwise |
| `test_semver_tag_from_string_invalid_returns_none` | `SemverTag.from_string("not-a-version", None)` → `None` |
| `test_semver_tag_lt_delegates` | Two `SemverTag` instances compare by their version |

### B. Real git repo tests — new test file `test_semver_integration.py`

All tests below use the `semver_repo` fixture. No mocks.

#### `bump` (live mode)

| Test | What it validates |
|---|---|
| `test_bump_major_creates_tag` | After bump major, `git tag -l` contains the new tag; version incremented correctly |
| `test_bump_minor_creates_tag` | Same for minor |
| `test_bump_patch_creates_tag` | Same for patch |
| `test_bump_prerelease_creates_tag` | Creates prerelease tag (e.g. `0.1.1-alpha1`) |
| `test_bump_sequential_prereleases` | Bump prerelease twice → `alpha1`, then `alpha2` |
| `test_bump_with_message` | Tag annotation includes the custom message |
| `test_bump_with_prefix` | Tag name includes the prefix (e.g. `v1.0.0`) |
| `test_bump_build_creates_tag` | Bump build creates tag with build metadata and SHA |
| `test_bump_build_no_sha` | `include_sha=False` → build tag without SHA |

#### `list`

| Test | What it validates |
|---|---|
| `test_list_release_only` | With mixed tags, `filter_type='release'` shows only releases |
| `test_list_prerelease_only` | `filter_type='prerelease'` shows only prereleases |
| `test_list_other_only` | `filter_type='other'` shows only non-semver tags |
| `test_list_all_shows_headers` | `filter_type='all'` prints section headers |
| `test_list_descending_order` | Highest version is first in output |
| `test_list_with_sha` | `show_sha=True` includes commit SHA next to each tag |
| `test_list_backwards_compat` | `list(release_type=PRERELEASE, filter_type='release')` → shows prerelease (backwards compat coercion) |

#### `get_current_semver`

| Test | What it validates |
|---|---|
| `test_get_current_semver_no_tags` | Repo with no semver tags → `None` |
| `test_get_current_semver_returns_highest` | With multiple tags (not in order), returns the highest |

#### `Semver.__init__` with `tag_string`

| Test | What it validates |
|---|---|
| `test_init_with_tag_string` | `Semver(tag_string="1.0.0\n2.0.0")` populates `tags` and `semver_tags` |

### C. Handler integration — extend `test_handlers.py`

These tests use the `semver_repo` fixture and call the handler functions with real `argparse.Namespace` objects, exercising the full path from handler → `Semver.with_tags_loaded()` → git.

| Test | What it validates |
|---|---|
| `test_handle_semver_no_subcommand` | Prints current release version to stdout |
| `test_handle_semver_no_subcommand_prerelease` | Prints current prerelease version |
| `test_handle_semver_bump_creates_tag` | Calls handler with `level='patch'`, `run=True` → tag exists in repo |
| `test_handle_semver_bump_dry_run` | `run=False` → prints command, no tag created |
| `test_handle_semver_list` | Calls handler → output matches `semver.list()` |
| `test_handle_semver_bump_build_no_version_exits` | Empty repo, bump build → `sys.exit(1)` |

## Summary

| Category | Count | Git repo needed? | Mocks? |
|---|---|---|---|
| A. SemverVersion/SemverTag pure logic | ~10 | No | No |
| B. Real git repo integration | ~16 | Yes (`semver_repo` fixture) | No |
| C. Handler integration | ~6 | Yes (`semver_repo` fixture) | No |
| Existing parser tests | (keep as-is) | No | No |
| **Total new** | **~32** | | **None** |

### Expected coverage outcome

With these tests, `semver.py` coverage should significantly increase (the `note`/`note_md`/`_determine_from_ref` paths will remain uncovered as they are out of scope). `tt_handlers.py` semver paths should go from 0% to near-full coverage of `handle_semver`, `_handle_semver_bump`, and `_handle_semver_bump_build`.
