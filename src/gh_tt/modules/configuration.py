import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

CONFIG_FILE_NAME = '.tt-config.json'


class ConfigParseError(Exception):
    """Raised when a config file contains malformed JSON."""


class ConfigValidationError(Exception):
    """Raised when config values fail Pydantic validation."""


class ConfigModel(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True)


class ProjectConfig(ConfigModel):
    owner: str | None = None
    number: int | None = None


class WorkonConfig(ConfigModel):
    status: str | None = None


class DeliverPolicies(ConfigModel):
    poll: bool = True


class DeliverConfig(ConfigModel):
    policies: DeliverPolicies = DeliverPolicies()


class TtConfig(ConfigModel):
    project: ProjectConfig = ProjectConfig()
    workon: WorkonConfig = WorkonConfig()
    deliver: DeliverConfig = DeliverConfig()


def _load_user_config(config_path: Path) -> dict:
    """Read a JSON file and return parsed dict.

    Raises:
        FileNotFoundError: if file does not exist.
        json.JSONDecodeError: if JSON is malformed.
    """
    with config_path.open() as f:
        return json.load(f)


def load_config(git_root: Path | None = None) -> TtConfig:
    """Build config by layering user config on top of defaults.

    If git_root is None, returns defaults only.
    """
    if git_root is None:
        return TtConfig()

    config_path = git_root / CONFIG_FILE_NAME
    if not config_path.exists():
        return TtConfig()

    try:
        user_data = _load_user_config(config_path)
    except json.JSONDecodeError as e:
        raise ConfigParseError(str(e)) from e

    try:
        return TtConfig.model_validate(user_data)
    except ValidationError as e:
        raise ConfigValidationError(str(e)) from e
