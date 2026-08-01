"""Throwaway: deliberately failing test to verify branch protection.

This file exists only to make CI red on a scratch branch, so we can observe
whether GitHub blocks the merge button. Delete this branch when done — it must
never reach main.
"""


def test_deliberately_failing_probe():
    assert False, "intentional failure: verifying that red CI blocks merging"
