"""Core module."""


class YourMainClass:
    """Main class description.

    Parameters
    ----------
    param1 : str
        Description of param1.
    param2 : int, optional
        Description of param2. Default: 10.
    """

    def __init__(self, param1: str, param2: int = 10) -> None:
        self.param1 = param1
        self.param2 = param2

    def do_something(self) -> str:
        """Do something and return a result."""
        return f"{self.param1}: {self.param2}"
