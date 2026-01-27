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


def test_register_circular_dependency_detected():
    # a <-> b, bidirectional dependency
    
    a = Command(name="a", command="", description="", depends_on=("b",))
    b = Command(name="b", command="", description="", depends_on=("a",))

    # not using register to avoid triggering assertion
    # about registering dependencies of a command first
    graph._commands["a"] = a

    with pytest.raises(AssertionError, match=r"Dependency cycle found"):
        graph.register(b)


def test_register_circular_dependency_detected_transitive():
    # a -> b -> c -> a, transitive dependency through b

    a = Command(name="a", command="", description="", depends_on=("b",))
    b = Command(name="b", command="", description="", depends_on=("c",))
    c = Command(name="c", command="", description="", depends_on=("a",))

    # not using register to avoid triggering assertion
    # about registering dependencies of a command first
    graph._commands["a"] = a
    graph._commands["b"] = b

    with pytest.raises(AssertionError, match=r"Dependency cycle found"):
        graph.register(c)


def test_register_all_success():
    graph.register(*ALL_COMMANDS)
