"""Example module containing a hello world function."""


def hello_world(name: str = "world") -> str:
    """Return a friendly greeting.

    Args:
        name: The name to greet. Defaults to "world".

    Returns:
        A greeting string of the form "Hello, {name}!".
    """
    return f"Hello, {name}!"
