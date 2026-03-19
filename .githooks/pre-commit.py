#!/usr/bin/env python3
"""Pre-commit hook that runs quality checks and reports results.

No check blocks the commit — this hook always exits 0.
"""

import subprocess
import time

CHECKS = [
    {'name': 'Unit tests', 'cmd': ['just', 'check-test']},
    {'name': 'Ruff format', 'cmd': ['just', 'check-format']},
    {'name': 'Ruff lint', 'cmd': ['just', 'check-lint']},
    {'name': 'ty type check', 'cmd': ['just', 'check-types']},
    {'name': 'cspell spell check', 'cmd': ['just', 'check-spelling']},
    {'name': 'actionlint', 'cmd': ['just', 'check-actionlint']},
    {'name': 'zizmor', 'cmd': ['just', 'check-zizmor']},
]


def run_check(check: dict) -> tuple[str, bool, str, float]:
    """Run a single check and return (name, passed, output, elapsed)."""
    start = time.monotonic()
    result = subprocess.run(
        check['cmd'],
        capture_output=True,
        text=True,
    )
    elapsed = time.monotonic() - start
    passed = result.returncode == 0
    output = (result.stdout + result.stderr).strip()
    return check['name'], passed, output, elapsed


def main() -> None:
    start = time.monotonic()
    results = [run_check(c) for c in CHECKS]
    elapsed = time.monotonic() - start

    print('Pre-commit checks:')
    failures = []
    for name, passed, output, check_time in results:
        icon = '✅' if passed else '⚠️'
        print(f'  {icon}  {name} ({check_time:.1f}s)')
        if not passed:
            failures.append((name, output))

    if failures:
        print()
        for name, output in failures:
            print(f'── {name} ──')
            print(output)
            print()

    print(f'Done in {elapsed:.1f}s')


if __name__ == '__main__':
    main()
