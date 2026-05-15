"""Smoke test to verify the package is importable end-to-end."""

import pytest

from goldfishmem import Memory, Provenance


@pytest.mark.integration
def test_package_importable() -> None:
    """Verify core types are importable from the top-level package."""
    assert Memory is not None
    assert Provenance is not None
