# Spec: Poll PR checks on `gh tt deliver --poll`

## Problem

When a user runs `gh tt deliver`, auto-merge is enabled on the PR but the user gets no feedback on whether the CI checks pass or fail. They must manually check GitHub to see the outcome.

## Goal

When `--poll` is passed (or the config default is set), continuously poll GitHub for the PR's check statuses until all checks reach a terminal state, printing live progress to the terminal.

## Scope

This spec covers only the `--pr-workflow` path in `handle_deliver`. The legacy `Devbranch`-based path already has its own `Status.poll()` mechanism.

## Design

### Data source

Use `gh pr checks <branch> --json name,state,bucket,workflow,link` to fetch check run data.

The relevant fields from the JSON response:

| Field      | Type   | Example values                                          |
|------------|--------|---------------------------------------------------------|
| `name`     | string | `"PR - tidy"`, `"Build"`                                |
| `state`    | string | `"PENDING"`, `"IN_PROGRESS"`, `"SUCCESS"`, `"FAILURE"`, `"SKIPPED"`, `"CANCELLED"`, `"STARTUP_FAILURE"`, `"STALE"`, `"ERROR"`, `"EXPECTED"` |
| `bucket`   | string | `"pending"`, `"pass"`, `"fail"`, `"skipping"`           |
| `workflow` | string | `"CI"`, `""`                                            |
| `link`     | string | URL to the check run                                    |

### Terminal vs non-terminal buckets

The `bucket` field already groups check states for us:

| Category     | Bucket values        |
|--------------|----------------------|
| Non-terminal | `pending`            |
| Terminal pass | `pass`, `skipping`  |
| Terminal fail | `fail`              |

Polling continues until no checks have `bucket == "pending"`.

### New code locations

1. **`gh_tt/commands/gh.py`** — add a Pydantic model and a function to fetch checks:

   ```python
   class CheckBucket(Enum):
       PENDING = "pending"
       PASS = "pass"
       FAIL = "fail"
       SKIPPING = "skipping"

   TERMINAL_BUCKETS = frozenset({CheckBucket.PASS, CheckBucket.FAIL, CheckBucket.SKIPPING})

   class Check(BaseModel):
       name: str
       bucket: CheckBucket
       workflow: str
       link: HttpUrl

   async def get_pr_checks(dev_branch: str) -> list[Check]:
       """Fetch the current check runs for the PR on dev_branch."""
   ```

2. **`gh_tt/deliver.py`** — add a `poll_checks` function called after `merge_pr`:

   ```python
   async def poll_checks(
       dev_branch: str,
       *,
       interval_seconds: int = 10,
       timeout_seconds: int = 900,  # 15 minutes
   ) -> bool:
       """Poll PR checks until all are terminal. Returns True if all passed."""
   ```

3. **`gh_tt/modules/tt_handlers.py`** — wire `args.poll` into the `pr_workflow` path of `handle_deliver`, respecting the config fallback.

### Output format

Each poll iteration prints a timestamped summary to stderr, for example:

```
[16:42:03] ⏳ 2/5 checks completed
  ✅ Calculate job matrix (CI)
  ✅ PR - tidy (CI)
  🔄 PR - pr-check-1 (CI)
  🔄 PR - x86_64-gnu-llvm-20 (CI)
  🔄 PR - pr-check-2 (CI)
```

On completion:

```
[16:45:12] ✅ All 5 checks passed
```

Or on failure:

```
[16:45:12] ❌ 1/5 checks failed
  ❌ PR - pr-check-1 (CI) — https://github.com/...
  ✅ PR - tidy (CI)
  ...
```

Key points:
- Timestamp (`HH:MM:SS`) is always printed even if the checks do not update.
- Terminal checks are sorted first (pass then fail), non-terminal last. Within each bucket, checks maintain their order.
- Failed checks include their `link` for quick access.
- Output goes to **stderr** so it doesn't interfere with the PR URL printed to stdout.

### Edge cases

| Scenario | Behavior |
|----------|----------|
| No checks exist on the PR | Print a message and return immediately (not an error) |
| Timeout reached | Print current state and exit with a non-zero code |
| Ctrl+C during polling | Catch `KeyboardInterrupt`, print out the url for all failed checks (one url per line), exit 0 (auto-merge is already enabled) |
| `gh pr checks` command fails | Raise `DeliverError` with the stderr from the command |


This matches the existing pattern used by the legacy path.

### Parameter flow

```
tt_parser.py          tt_handlers.py          deliver.py             commands/gh.py
────────────          ──────────────          ──────────             ──────────────
args.poll ──────────► handle_deliver()
                      resolve poll flag
                      (CLI > config > false)
                          │
                          ▼
                      asyncio.run(
                        deliver(
                          delete_branch=...,
                          poll=True/False    ──► if poll:
                        )                         poll_checks(branch)
                      )                             │
                                                    ▼
                                               get_pr_checks(branch) ◄── gh pr checks ...
```

### Testing

**Unit tests** (mock `shell.run`):
- All checks pass → returns `True`
- Some checks fail → returns `False`
- No checks → returns `True` immediately
- Timeout → returns `False`
- Correct output formatting (timestamps, icons, sorting)

**End-to-end tests**:
- Not practical to test polling in e2e since test repos have no CI configured. The existing `test_workon_deliver_flow_success` already validates the core deliver flow; polling is additive.

### Out of scope

- Making `--poll` the default (to be decided later)
- Polling for the `wrapup` command
- Custom interval/timeout CLI flags (can use config if needed later)
- Config fallback


Config fallback

The `--poll` / `--no-poll` CLI flags take precedence. When neither is passed (`args.poll is None`), fall back to `.tt-config.json`:

```json
{
  "deliver": {
    "policies": {
      "poll": true
    }
  }
}
```