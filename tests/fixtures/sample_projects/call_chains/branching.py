"""Branching call chains for testing call complexity analysis.

Call chains:
- orchestrate() → worker_a() → task_a() (depth=2)
- orchestrate() → worker_b() → task_b1() → task_b2() (depth=3)
- orchestrate() → direct_task() (depth=1)

Tests:
- orchestrate: max depth = 3 (longest branch through worker_b)
- worker_a: max depth = 1
- worker_b: max depth = 2
"""


def orchestrate(data: dict) -> dict:
    """Orchestrates multiple workers - branches to different depths."""
    result_a = worker_a(data["a"])
    result_b = worker_b(data["b"])
    result_c = direct_task(data["c"])
    return {"a": result_a, "b": result_b, "c": result_c}


def worker_a(value: int) -> int:
    """Worker A - calls one level deep."""
    return task_a(value)


def worker_b(value: int) -> int:
    """Worker B - calls two levels deep."""
    return task_b1(value)


def task_a(value: int) -> int:
    """Task A - leaf."""
    return value + 1


def task_b1(value: int) -> int:
    """Task B1 - calls task_b2."""
    return task_b2(value)


def task_b2(value: int) -> int:
    """Task B2 - leaf."""
    return value * 2


def direct_task(value: str) -> str:
    """Direct task - leaf."""
    return value.upper()
