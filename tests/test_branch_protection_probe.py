"""Throwaway: deliberately failing test to verify branch protection.

This file exists only to make CI red on a scratch branch, so we can observe
whether GitHub blocks the merge button. Delete this branch when done — it must
never reach main.

It raises AssertionError directly rather than using `assert False`, which ruff
rejects under B011 (`python -O` strips bare asserts). The point is to fail the
*test* step, not the lint step.
"""


def test_deliberately_failing_probe():
    raise AssertionError("intentional failure: verifying that red CI blocks merging")
