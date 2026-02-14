"""Tests for core module."""

from your_package.core import YourMainClass


def test_do_something() -> None:
    """Test YourMainClass.do_something returns expected string."""
    obj = YourMainClass(param1="hello", param2=5)
    assert obj.do_something() == "hello: 5"


def test_default_param2() -> None:
    """Test default value of param2."""
    obj = YourMainClass(param1="test")
    assert obj.param2 == 10
