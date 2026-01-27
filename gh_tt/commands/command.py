import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

type Parameter = tuple[str, type]
type CommandOutput = str


@dataclass(frozen=True)
class Command:
    """Shell command with optional dependencies."""

    name: str
    command: str
    description: str
    depends_on: tuple[str, ...] | None = None
    params: tuple[Parameter, ...] = field(default_factory=tuple)
    parser: Callable[[CommandOutput], dict[str, Any]] | None = None
    outputs: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self):
        """Validate command configuration."""

        assert self.parser is None or self.outputs, (
            f"Command '{self.name}': parser requires outputs to be defined"
        )

        assert self.outputs == () or self.parser is not None, (
            f"Command '{self.name}': outputs require a parser to be defined"
        )

        output_equals_name = [o for o in self.outputs if o == self.name]
        assert not output_equals_name, (
            f"No output can be named as the command. Violating output(s): '{output_equals_name}'"
        )

        self._validate_substitution()

    def _validate_substitution(self):
        placeholders = re.findall(r"\{(\w+)\}", self.command)
        assert len(placeholders) == len(set(placeholders)), "Placeholders must be unique"

        # Collect all valid placeholder names
        valid_placeholders = set()
        param_names = [param_name for param_name, _ in self.params]
        if self.depends_on:
            valid_placeholders.update(self.depends_on)
        valid_placeholders.update(param_names)

        # Check all placeholders are valid
        invalid_placeholders = set(placeholders) - valid_placeholders
        assert not invalid_placeholders, (
            f"Command '{self.name}': placeholders {invalid_placeholders} are not defined in depends_on or params. All placeholders must be replaced from either a declared dependency or an input parameter."
        )

    # TODO: test
    def format(self, dependency_results: dict[str, str], params: dict[str, Any]) -> str:
        """Substitute placeholders with resolved values."""

        values = dependency_results | params

        result = self.command
        for key, value in values.items():
            result = result.replace(f"{{{key}}}", str(value))

        assert re.match(r"\{(\w+)\}", result) is None, (
            f"Formatting command '{self.name}' failed. All placeholders must be replaced with values."
        )
        return result

    def __hash__(self):
        return hash(self.name)
