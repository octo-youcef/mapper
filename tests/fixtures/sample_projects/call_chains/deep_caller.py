"""Deep call chain for testing call complexity analysis.

Call chain: start() → level1() → level2() → level3() → level4() → level5()
Maximum depth: 5 levels
"""


def start(data: str) -> str:
    """Entry point - triggers deep call chain."""
    return level1(data)


def level1(data: str) -> str:
    """First level of call chain."""
    return level2(data)


def level2(data: str) -> str:
    """Second level of call chain."""
    return level3(data)


def level3(data: str) -> str:
    """Third level of call chain."""
    return level4(data)


def level4(data: str) -> str:
    """Fourth level of call chain."""
    return level5(data)


def level5(data: str) -> str:
    """Fifth level - leaf function."""
    return data.upper()
