import pytest

from gh_tt.__main__ import is_version_sufficient, parse_version


@pytest.mark.parametrize(
    ('version', 'expected'),
    [
        ('2.55.0', (2, 55, 0)),
        ('2.100.0', (2, 100, 0)),
        ('2.54.9', (2, 54, 9)),
        ('3.0.0', (3, 0, 0)),
    ],
)
def test_parse_version(version, expected):
    assert parse_version(version) == expected


@pytest.mark.parametrize(
    ('actual', 'required', 'expected'),
    [
        ('2.55.0', '2.55.0', True),  # exact match
        ('2.56.0', '2.55.0', True),  # minor bump above
        ('2.100.0', '2.55.0', True),  # large minor, would fail lexicographic comparison
        ('3.0.0', '2.55.0', True),  # major bump
        ('2.54.9', '2.55.0', False),  # patch below
        ('2.54.0', '2.55.0', False),  # minor below
        ('1.99.0', '2.55.0', False),  # major below
    ],
)
def test_is_version_sufficient(actual, required, expected):
    assert is_version_sufficient(actual, required) == expected
