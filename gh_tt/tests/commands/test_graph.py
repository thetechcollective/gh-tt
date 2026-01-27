import asyncio

import pytest

from gh_tt.commands.command import Command
from gh_tt.commands.definitions import ALL_COMMANDS
from gh_tt.commands.graph import CommandGraph

pytestmark = pytest.mark.unittest

def test_register_command_success():
    graph = CommandGraph()
    command = Command(name="name", description="test", command="echo 'test'")

    result = graph.register(command)

    assert result["name"] == command
    assert len(graph.commands) == 1

    assert isinstance(graph._locks["name"], asyncio.Lock)
    assert len(graph._locks) == 1


def test_register_command_deps_order():
    graph = CommandGraph()
    command = Command(
        name="name", description="test", command="echo 'test'", depends_on=["some_dep"]
    )

    with pytest.raises(AssertionError, match=r"^Dependency 'some_dep'"):
        graph.register(command)


def test_register_all_success():
    CommandGraph().register(*ALL_COMMANDS)