import string

import pytest
from hypothesis import given
from hypothesis import strategies as st

from gh_tt.commands.command import Command

pytestmark = pytest.mark.unittest


@given(
    name=st.text(),
    command=st.text(),
    description=st.text(),
    depends_on=st.lists(st.text()),
    outputs=st.dictionaries(
        keys=st.text(min_size=1),
        values=st.sampled_from([str, int, dict, tuple, float]),
        min_size=1,
    ),
)
def test_validation_fails_when_outputs_without_parser(
    name, command, description, depends_on, outputs
):
    with pytest.raises(AssertionError, match="outputs require a parser"):
        Command(
            name=name,
            command=command,
            description=description,
            depends_on=tuple(depends_on),
            outputs=outputs,
        )


@given(
    name=st.text(),
    command=st.text(),
    description=st.text(),
    depends_on=st.lists(st.text()),
    parser=st.functions(
        like=lambda _: {}, returns=st.dictionaries(keys=st.text(), values=st.text())
    ),
)
def test_validation_fails_when_parser_without_outputs(
    name, command, description, depends_on, parser
):
    with pytest.raises(AssertionError, match="parser requires outputs"):
        Command(
            name=name,
            command=command,
            description=description,
            depends_on=tuple(depends_on),
            parser=parser,
        )


@given(
    name=st.text(),
    description=st.text(),
    placeholder=st.text(min_size=1, alphabet=string.ascii_letters),
)
def test_placeholders_unique(name, description, placeholder):
    with pytest.raises(AssertionError, match="must be unique"):
        Command(
            name=name,
            command=f"command {{{placeholder}}} {{{placeholder}}}",
            description=description,
            depends_on="",
            params={placeholder: str},
        )


@given(
    name=st.text(),
    description=st.text(),
    placeholder=st.text(min_size=1, alphabet=string.ascii_letters),
)
def test_placeholders_defined_in_params_or_deps(name, description, placeholder):
    with pytest.raises(AssertionError, match=r"not defined in depends_on or params"):
        Command(
            name=name,
            command=f"command {{{placeholder}}}",
            description=description,
        )


@given(
    name=st.text(),
    command=st.text(),
    description=st.text(),
)
def test_output_names_are_not_command_name(name, description, command):
    with pytest.raises(AssertionError, match=r"can be named as the command"):
        Command(
            name=name,
            command=command,
            description=description,
            outputs={name: str},
            parser=lambda _: {},
        )
