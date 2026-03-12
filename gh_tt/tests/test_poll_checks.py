import pytest
from pydantic import HttpUrl

from gh_tt.commands.gh import Check, CheckBucket
from gh_tt.deliver import (
    DeliverError,
    _format_check_line,
    _sort_checks,
    poll_checks,
)
from gh_tt.shell import ShellError


def _make_check(name: str, bucket: CheckBucket, workflow: str = 'CI') -> Check:
    return Check(
        name=name,
        bucket=bucket,
        workflow=workflow,
        link=HttpUrl(f'https://example.com/run/{name}'),
    )


@pytest.mark.unittest
def test_format_check_line_pass():
    check = _make_check('Build', CheckBucket.PASS)
    assert '✅' in _format_check_line(check)
    assert 'Build (CI)' in _format_check_line(check)


@pytest.mark.unittest
def test_format_check_line_fail_includes_link():
    check = _make_check('Build', CheckBucket.FAIL)
    line = _format_check_line(check)
    assert '❌' in line
    assert str(check.link) in line


@pytest.mark.unittest
def test_format_check_line_pending():
    check = _make_check('Build', CheckBucket.PENDING)
    assert '🔄' in _format_check_line(check)


@pytest.mark.unittest
def test_format_check_line_skipping():
    check = _make_check('Build', CheckBucket.SKIPPING)
    assert '⏭️' in _format_check_line(check)


@pytest.mark.unittest
def test_sort_checks_order():
    checks = [
        _make_check('pending', CheckBucket.PENDING),
        _make_check('fail', CheckBucket.FAIL),
        _make_check('pass', CheckBucket.PASS),
        _make_check('skip', CheckBucket.SKIPPING),
    ]
    sorted_checks = _sort_checks(checks)
    assert [c.name for c in sorted_checks] == ['pass', 'skip', 'fail', 'pending']


@pytest.mark.unittest
async def test_poll_checks_all_pass(mocker):
    checks = [
        _make_check('Build', CheckBucket.PASS),
        _make_check('Lint', CheckBucket.PASS),
    ]
    mocker.patch('gh_tt.deliver.gh.get_pr_checks', return_value=checks)

    result = await poll_checks('dev', interval_seconds=0)

    assert result is True


@pytest.mark.unittest
async def test_poll_checks_some_fail(mocker):
    checks = [
        _make_check('Build', CheckBucket.PASS),
        _make_check('Lint', CheckBucket.FAIL),
    ]
    mocker.patch('gh_tt.deliver.gh.get_pr_checks', return_value=checks)

    result = await poll_checks('dev', interval_seconds=0)

    assert result is False


@pytest.mark.unittest
async def test_poll_checks_no_checks_returns_true(mocker):
    mocker.patch('gh_tt.deliver.gh.get_pr_checks', return_value=[])

    result = await poll_checks('dev', interval_seconds=0, no_checks_retries=0)

    assert result is True


@pytest.mark.unittest
async def test_poll_checks_retries_before_reporting_no_checks(mocker):
    checks = [_make_check('Build', CheckBucket.PASS)]
    mock = mocker.patch('gh_tt.deliver.gh.get_pr_checks', side_effect=[[], [], checks])

    result = await poll_checks('dev', interval_seconds=0, no_checks_retries=3)

    assert result is True
    assert mock.call_count == 3


@pytest.mark.unittest
async def test_poll_checks_retries_gives_up(mocker, capsys):
    checks = [_make_check('Build', CheckBucket.PASS)]
    mocker.patch('gh_tt.deliver.gh.get_pr_checks', side_effect=[[], [], checks])

    result = await poll_checks('dev', interval_seconds=0, no_checks_retries=1)

    assert result is True

    captured = capsys.readouterr()
    assert captured.out == ''
    assert 'No checks found' in captured.err


@pytest.mark.unittest
async def test_poll_checks_timeout_returns_false(mocker):
    checks = [_make_check('Build', CheckBucket.PENDING)]
    mocker.patch('gh_tt.deliver.gh.get_pr_checks', return_value=checks)

    result = await poll_checks('dev', interval_seconds=0, timeout_seconds=0)

    assert result is False


@pytest.mark.unittest
async def test_poll_checks_polls_until_terminal(mocker):
    pending = [_make_check('Build', CheckBucket.PENDING)]
    done = [_make_check('Build', CheckBucket.PASS)]

    mocker.patch('gh_tt.deliver.gh.get_pr_checks', side_effect=[pending, pending, done])

    result = await poll_checks('dev', interval_seconds=0)

    assert result is True


@pytest.mark.unittest
async def test_poll_checks_shell_error_raises_deliver_error(mocker):
    mocker.patch(
        'gh_tt.deliver.gh.get_pr_checks',
        side_effect=ShellError(
            cmd=['gh', 'pr', 'checks'],
            stdout='',
            stderr='not found',
            return_code=1,
        ),
    )

    with pytest.raises(DeliverError, match='not found'):
        await poll_checks('dev', interval_seconds=0)


@pytest.mark.unittest
async def test_poll_checks_output_goes_to_stderr(mocker, capsys):
    checks = [
        _make_check('Build', CheckBucket.PASS),
        _make_check('Lint', CheckBucket.FAIL),
    ]
    mocker.patch('gh_tt.deliver.gh.get_pr_checks', return_value=checks)

    await poll_checks('dev', interval_seconds=0)

    captured = capsys.readouterr()
    assert captured.out == ''
    assert '❌' in captured.err
    assert 'Build' in captured.err


@pytest.mark.unittest
async def test_poll_checks_no_checks_message_to_stderr(mocker, capsys):
    mocker.patch('gh_tt.deliver.gh.get_pr_checks', return_value=[])

    await poll_checks('dev', interval_seconds=0, no_checks_retries=0)

    captured = capsys.readouterr()
    assert captured.out == ''
    assert 'No checks found' in captured.err
