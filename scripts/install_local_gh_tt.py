#!/usr/bin/env python3

"""
Removes whatever version of gh-tt you have installed and installs the local version.

The local version of gh-tt is needed for run end-to-end tests from your machine.
"""

import subprocess
import sys
from pathlib import Path

EXTENSION = 'gh-tt'


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print(f'→ {" ".join(cmd)}')
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def main() -> None:
    # Ensure gh CLI is available
    if run(['gh', '--version'], check=False).returncode != 0:
        print('ERROR: gh CLI not found in PATH', file=sys.stderr)
        sys.exit(1)

    # Get repo root from git
    result = run(['git', 'rev-parse', '--show-toplevel'], check=False)
    if result.returncode != 0:
        print('ERROR: not inside a git repository', file=sys.stderr)
        sys.exit(1)
    repo_root = Path(result.stdout.strip())

    # Remove existing extension (ignore errors if not installed)
    result = run(['gh', 'extension', 'remove', EXTENSION], check=False)
    if result.returncode == 0:
        print(f'Removed existing {EXTENSION} extension')
    else:
        print(f'{EXTENSION} was not installed — nothing to remove')

    # Install from local checkout (must run from repo root)
    result = run(['gh', 'extension', 'install', '.'], check=False)
    if result.returncode != 0:
        print(f'ERROR: failed to install local {EXTENSION}', file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)

    print(f'Successfully installed local {EXTENSION} from {repo_root}')


if __name__ == '__main__':
    main()
