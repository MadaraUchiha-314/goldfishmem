"""Tests for goldfishmem.hello."""

from goldfishmem import hello_world


def test_hello_world_default() -> None:
    assert hello_world() == "Hello, world!"


def test_hello_world_with_name() -> None:
    assert hello_world("goldfish") == "Hello, goldfish!"
