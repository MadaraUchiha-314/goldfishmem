"""Example integration test.

Integration tests live in `tests/integration/` and run against real external
dependencies. They are run separately from unit tests in CI.
"""

import pytest

from goldfishmem import hello_world


@pytest.mark.integration
def test_hello_world_integration_smoke() -> None:
    """Smoke test to verify the package is importable and callable end-to-end."""
    assert hello_world("integration") == "Hello, integration!"
