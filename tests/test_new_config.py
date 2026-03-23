import json
import tempfile
from contextlib import nullcontext as does_not_raise
from pathlib import Path

import pytest

from gh_tt.modules.configuration import (
    ConfigParseError,
    ConfigValidationError,
    ProjectConfig,
    TtConfig,
    load_config,
)


def test_default_values():
    config = TtConfig()
    assert config.project.owner is None
    assert config.project.number is None

    assert config.workon.status is None

    assert config.deliver.policies.poll is True


def test_config_models_are_immutable():
    config = TtConfig()
    with pytest.raises(Exception, match='frozen'):
        config.project = ProjectConfig()

    with pytest.raises(Exception, match='frozen'):
        config.deliver.policies.poll = True

    with pytest.raises(Exception, match='frozen'):
        config.workon.status = 'Test'


def test_no_git_root_returns_defaults():
    config = load_config(git_root=None)
    assert config == TtConfig()


def test_missing_config_file_returns_defaults():
    with tempfile.TemporaryDirectory() as temp_dir:
        config = load_config(Path(temp_dir))
        assert config == TtConfig()


def test_partial_override_retains_untouched_defaults():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        (temp_dir / '.tt-config.json').write_text(json.dumps({'workon': {'status': 'Todo'}}))

        default_config = load_config(git_root=None)
        config = load_config(git_root=temp_dir)

        assert config.workon.status == 'Todo', 'Expected to load user-defined config value'

        default_config_dump = default_config.model_dump()
        config_dump = config.model_dump()

        # Patch the only value that should be changed from the default config
        # all other values should retain their defaults
        default_config_dump['workon']['status'] = 'Todo'

        assert config_dump == default_config_dump, (
            'Expected patched defaults and parsed config to match'
        )


@pytest.mark.parametrize(
    ('config_content', 'expectation'),
    [
        ('{ bad json }', pytest.raises(ConfigParseError)),
        (json.dumps({'project': {'number': 'abc'}}), pytest.raises(ConfigValidationError)),
        (
            json.dumps({'deliver': {'policies': {'poll': 'yes'}}}),
            pytest.raises(ConfigValidationError),
        ),
        (json.dumps({'unknown_field': 'should_be_ignored'}), does_not_raise()),
    ],
)
def test_config_parsing_raises_correct_exception(config_content: str, expectation):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        (temp_dir / '.tt-config.json').write_text(config_content)

        with expectation:
            load_config(git_root=temp_dir)
