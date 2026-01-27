import asyncio
from dataclasses import dataclass, field
from typing import Any

from gh_tt.classes.gitter import Gitter
from gh_tt.commands.command import Command

type CommandDefinitions = dict[str, Command]
type CacheKey = tuple[str, frozenset[tuple[str, Any]]]
type CachedResults = dict[CacheKey, Any]
type CommandLocks = dict[str, asyncio.Lock]


@dataclass
class CommandGraph:
    commands: CommandDefinitions = field(default_factory=dict)
    results: CachedResults = field(default_factory=dict)
    _locks: CommandLocks = field(default_factory=dict)

    verbose: bool = False

    def register(self, *commands: Command) -> CommandDefinitions:
        for cmd in commands:
            assert cmd.name not in self.commands, f"Command '{cmd.name}' already registered"

            if cmd.depends_on is None:
                self.commands[cmd.name] = cmd
                self._locks[cmd.name] = asyncio.Lock()
                continue

            for d in cmd.depends_on:
                assert d in self.commands, (
                    f"Dependency '{d}' of command '{cmd.name}' is not registered. Dependencies must be registered before commands that depend on them."
                )

            self.commands[cmd.name] = cmd
            self._locks[cmd.name] = asyncio.Lock()

        return self.commands

    async def resolve(self, name: str, *, cache: bool = True, **kwargs) -> str | dict[str, Any]:
        cmd = self._get_command(name)
        assert cmd, f"Command '{name}' is not registered, and not an output of any command"
        assert cmd.name in self._locks, f"Lock for command '{cmd.name}' is missing"

        supplied_params = dict(kwargs.items())
        self._validate_params(cmd, supplied_params)

        cache_key = self._cache_key(name, supplied_params)

        async with self._locks[cmd.name]:
            # Check cache inside the lock to avoid duplicate execution
            if cache and cache_key in self.results:
                return self.results[cache_key]

            if cmd.depends_on:
                await asyncio.gather(*[self.resolve(dep) for dep in cmd.depends_on])

            cmd_str = cmd.format(dependency_results=self.results, params=supplied_params)

            await Gitter.fetch()

            raw, _ = await Gitter(
                cmd=cmd_str, msg=cmd.description, die_on_error=True, verbose=self.verbose
            ).run()

            result = cmd.parser(raw) if cmd.parser else raw

            if not cache:
                return result

            if cmd.outputs:
                for key in cmd.outputs:
                    output = result.get(key)
                    if output is None:
                        raise RuntimeError(f"Resolving '{name}' failed for output '{key}'.")

                    assert isinstance(output, cmd.outputs[output]), (
                        f"Expected output type to be '{cmd.outputs[output].__name__}', but got {type(output).__name__}"
                    )

                    output_key = self._cache_key(key, supplied_params)
                    self.results[output_key] = result[key]

                # Cache the whole result of the parser under the command key
                cmd_key = self._cache_key(cmd.name, supplied_params)
                self.results[cmd_key] = result

                # When a command has outputs, return the whole return value of the parser
                return result

            # Command has no declared outputs -> save and return the result of the command
            self.results[cache_key] = result
            return self.results[cache_key]

    def _cache_key(self, name: str, params: dict[str, Any]) -> CacheKey:
        """Generate a composite cache key from name and parameters."""
        return (name, frozenset(params.items()))

    def _get_command(self, name: str) -> Command | None:
        """Get which command needs to be resolved"""

        if name in self.commands:
            return self.commands[name]

        for cmd in self.commands.values():
            if name in cmd.outputs:
                return cmd

        return None

    def _validate_params(self, cmd: Command, supplied_params: dict[str, Any]):
        # Assert that all parameters needed for the command were passed in
        missing = [
            parameter_name
            for parameter_name, _ in cmd.params
            if parameter_name not in supplied_params
        ]
        assert not missing, f"Command '{cmd.name}' missing required params: {missing}"

        for supplied_param, value in supplied_params.items():
            expected_type = [t for p, t in cmd.params if p == supplied_param]
            assert expected_type, (
                f"Command '{cmd.name}' does not declare parameter '{supplied_param}'. "
                f"Declared parameters: {[p for p, _ in cmd.params]}"
            )
            assert len(expected_type) == 1, (
                f"Found two or more types for a declared parameter: '{expected_type}'. Parameters must be unique - and therefore only one type should be returned."
            )
            assert isinstance(value, expected_type[0]), (
                f"Command '{cmd.name}' parameter '{supplied_param}' expects type {expected_type[0].__name__}, but got {type(value).__name__}"
            )
