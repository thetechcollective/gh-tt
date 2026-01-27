import asyncio

import pytest

from gh_tt.commands import graph
from gh_tt.commands.command import Command
from gh_tt.commands.definitions import ALL_COMMANDS


@pytest.fixture(autouse=True)
def reset_graph():
    """Reset module state before each test."""
    graph.reset()
    yield
    graph.reset()

pytestmark = pytest.mark.unittest


def test_register_command_success():
    command = Command(name="name", description="test", command="echo 'test'")

    result = graph.register(command)

    assert result["name"] == command
    assert len(graph._commands) == 1

    assert isinstance(graph._locks["name"], asyncio.Lock)
    assert len(graph._locks) == 1


def test_register_command_deps_order():
    command = Command(
        name="name", description="test", command="echo 'test'", depends_on=["some_dep"]
    )

    with pytest.raises(AssertionError, match=r"^Dependency 'some_dep'"):
        graph.register(command)


def test_register_all_success():
    graph.register(*ALL_COMMANDS)
