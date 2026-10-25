import pytest
from _mocks.fake_text import FakeTextModel


@pytest.fixture
def fake_text() -> FakeTextModel:
    return FakeTextModel()


@pytest.fixture
def flaky_text() -> FakeTextModel:
    """One verifier disagreement on the first resolution, cleared by the rewrite round."""
    return FakeTextModel(fail_reference='ref L01', fail_reference_rounds=1)


@pytest.fixture
def stubborn_text() -> FakeTextModel:
    """Disagrees on every round, so the anchor must be discarded."""
    return FakeTextModel(fail_reference='ref L01', fail_reference_rounds=99)
