import os

import pytest
from hypothesis import settings

from gh_tt import shell

# Hypothesis profiles
# To run e.g. the "a_lot" profile --> `pytest -m hypothesis --hypothesis-profile a_lot`

settings.register_profile('1000', max_examples=1000)
settings.register_profile('10000', max_examples=10000)
settings.register_profile('100000', max_examples=100000)

def is_gh_actions() -> bool:
    return os.getenv('GITHUB_ACTIONS') is not None

def pytest_sessionstart(session: pytest.Session):
    print(session)
    return
    


@pytest.fixture(
        scope="session",
        # Abuse fixture parametrization to apply the end_to_end mark to all tests that require this fixture
        params=[pytest.param("", marks=pytest.mark.end_to_end)]
)
async def check_end_to_end_env():
    if is_gh_actions():
        # Assume environment is setup correctly in CI
        return
    
    result = await shell.run(['gh', 'auth', 'status'], die_on_error=False)
    assert result.return_code == 0, (
        'gh CLI is not authenticated. Run: gh auth login'
    )

    result = await shell.run(['gh', 'org', 'list'])
    orgs = result.stdout
    assert 'gh-tt-qa' in orgs, 'You must have access to the gh-tt-qa organization to trigger integration tests locally. Contact a maintainer of gh-tt for access.'

    result = await shell.run(['gh', 'extension', 'list'])
    extensions = result.stdout

    assert 'thetechcollective/gh-tt' not in extensions, 'You have a remote version of the gh-tt extension installed. To trigger an integration test run, you must install a local version of the extension. Install the local version with\ngh ext remove thetechcollective/gh-tt && gh ext install .'
    assert 'gh tt' in extensions, 'gh tt is not installed. Install with\ngh extension install .'