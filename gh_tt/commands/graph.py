import asyncio
from typing import Any

from gh_tt.classes.gitter import Gitter
from gh_tt.commands.command import Command

type CommandDefinitions = dict[str, Command]
type CacheKey = tuple[str, frozenset[tuple[str, Any]]]
type CachedResults = dict[CacheKey, Any]
type CommandLocks = dict[str, asyncio.Lock]

# Module-level state
_commands: CommandDefinitions = {}
_results: CachedResults = {}
_locks: CommandLocks = {}
_verbose: bool = False


def register(*commands: Command) -> CommandDefinitions:
    for cmd in commands:
        assert cmd.name not in _commands, f"Command '{cmd.name}' already registered"

        if cmd.depends_on is None:
            _commands[cmd.name] = cmd
            _locks[cmd.name] = asyncio.Lock()
            continue

        for d in cmd.depends_on:
            assert d in _commands, (
                f"Dependency '{d}' of command '{cmd.name}' is not registered. Dependencies must be registered before commands that depend on them."
            )

        has_cycle, cmd_name, dep = _has_cycle(cmd.name, cmd.depends_on)
        assert not has_cycle, (
            f"Dependency cycle found: '{cmd_name}' -> '{dep}'. Dependencies must not have cycles."
        )

        _commands[cmd.name] = cmd
        _locks[cmd.name] = asyncio.Lock()

    return _commands


def _has_cycle(name: str, depends_on: tuple[str, ...], visited: set[str] | None = None):
    """DFS cycle detection at registration time."""
    visited = visited or {name}
    for dep in depends_on:
        if dep in visited:
            return True, name, dep

        if dep in _commands and _commands[dep].depends_on:
            result = _has_cycle(dep, _commands[dep].depends_on, visited | {dep})
            if result[0]:
                return result

    return False, None, None


async def resolve(name: str, *, cache: bool = True, **kwargs) -> str | dict[str, Any]:
    cmd = _get_command(name)
    assert cmd, f"Command '{name}' is not registered, and not an output of any command"
    assert cmd.name in _locks, f"Lock for command '{cmd.name}' is missing"

    supplied_params = dict(kwargs.items())
    _validate_params(cmd, supplied_params)

    cache_key = _cache_key(name, supplied_params)

    async with _locks[cmd.name]:
        # Check cache inside the lock to avoid duplicate execution
        if cache and cache_key in _results:
            return _results[cache_key]

        if cmd.depends_on:
            await asyncio.gather(*[resolve(dep) for dep in cmd.depends_on])

        cmd_str = cmd.format(dependency_results=_results, params=supplied_params)

        await Gitter.fetch()

        raw, _ = await Gitter(
            cmd=cmd_str, msg=cmd.description, die_on_error=True, verbose=_verbose
        ).run()

        result = cmd.parser(raw) if cmd.parser else raw

        if not cache:
            return result

        if cmd.outputs:
            for key in cmd.outputs:
                output = result.get(key)
                if output is None:
                    raise RuntimeError(f"Resolving '{name}' failed for output '{key}'.")

                assert isinstance(output, cmd.outputs[key]), (
                    f"Expected output '{key}' type to be '{cmd.outputs[key].__name__}', but got {type(output).__name__}"
                )

                output_key = _cache_key(key, supplied_params)
                _results[output_key] = result[key]

            # Cache the whole result of the parser under the command key
            cmd_key = _cache_key(cmd.name, supplied_params)
            _results[cmd_key] = result

            # When a command has outputs, return the whole return value of the parser
            return result

        # Command has no declared outputs -> save and return the result of the command
        _results[cache_key] = result
        return _results[cache_key]


def reset():
    """Reset all module state. Primarily for testing."""
    global _commands, _results, _locks, _verbose
    _commands = {}
    _results = {}
    _locks = {}
    _verbose = False


def set_verbose(*, verbose: bool):
    """Set verbose mode for command execution."""
    global _verbose
    _verbose = verbose


def _cache_key(name: str, params: dict[str, Any]) -> CacheKey:
    """Generate a composite cache key from name and parameters."""
    return (name, frozenset(params.items()))


def _get_command(name: str) -> Command | None:
    """Get which command needs to be resolved"""

    if name in _commands:
        return _commands[name]

    for cmd in _commands.values():
        if name in cmd.outputs:
            return cmd

    return None


def _validate_params(cmd: Command, supplied_params: dict[str, Any]):
    # Assert that all parameters needed for the command were passed in
    missing = [
        parameter_name for parameter_name, _ in cmd.params if parameter_name not in supplied_params
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
