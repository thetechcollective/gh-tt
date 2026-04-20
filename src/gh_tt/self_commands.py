"""
This module contains code for `self` commands, like `gh tt self upgrade`.

It is named self_commands.py rather than self to prevent shadowing Python's class instance reference.
"""

from gh_tt.commands import shell


async def upgrade(pin: str):
    result = await shell.run(['gh', 'ext', 'list'])
    extensions = result.stdout

    assert 'gh-tt' in extensions, 'Expected gh-tt to be installed'
    await shell.run(['gh', 'ext', 'remove', 'gh-tt'])

    await shell.run(
        [
            'gh',
            'extension',
            'install',
            'thetechcollective/gh-tt',
            '--pin',
            pin,
        ]
    )
