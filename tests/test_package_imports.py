import your_package


def test_package_exposes_version() -> None:
    assert isinstance(your_package.__version__, str)
