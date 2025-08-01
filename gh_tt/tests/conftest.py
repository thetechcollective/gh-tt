from dataclasses import dataclass

import pytest


@dataclass
class FakeProcessResult:
    returncode: int = 0
    stderr: str = ""
    stdout: str = ""

@dataclass
class FakeGitter:
    responses: list[FakeProcessResult]
    call_count: int = 0
    
    def __post_init__(self):
        self._responses_iter = iter(self.responses)

    def run(self):
        self.call_count += 1

        try:
            process_result = next(self._responses_iter)

            return (process_result.stdout, process_result)
        except StopIteration as e:
            raise AssertionError("More calls to 'run' were made than there were configured responses.") from e

@pytest.fixture
def gitter():
    def _gitter(returncode: int | None = None, stdout: str | None = None, stderr: str | None = None):
        return FakeGitter([FakeProcessResult(returncode=returncode, stdout=stdout, stderr=stderr)
        ])
    
    return _gitter

@pytest.fixture
def gitter_many():
    def _gitter(responses: list[FakeGitter]):
        return FakeGitter(responses=responses)
    
    return _gitter