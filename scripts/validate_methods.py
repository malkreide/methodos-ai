"""Validate every method JSON in /methods/ against the Pydantic Method model.

Used by:
  * pre-commit hook (fast local feedback)
  * CI workflow `pr-method-validate.yml` on PRs touching methods/**
  * manual: `python scripts/validate_methods.py`

Exit codes:
  0  - all methods valid
  1  - at least one validation error (all errors printed before exit)
  2  - usage error (e.g. methods/ does not exist)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

from methodos.models import Method


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--methods-dir",
        type=Path,
        default=Path("methods"),
        help="Directory containing method JSON files (default: methods/)",
    )
    args = parser.parse_args()

    if not args.methods_dir.is_dir():
        print(f"error: {args.methods_dir} is not a directory", file=sys.stderr)
        return 2

    files = sorted(args.methods_dir.glob("*.json"))
    if not files:
        print(f"warning: no JSON files found in {args.methods_dir}")
        return 0

    errors: list[str] = []
    seen_ids: dict[str, Path] = {}

    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{path}: invalid JSON: {e}")
            continue

        try:
            method = Method.model_validate(data)
        except ValidationError as e:
            errors.append(f"{path}: {e}")
            continue

        if path.stem != method.id:
            errors.append(
                f"{path}: filename stem '{path.stem}' must equal id '{method.id}' (mismatch)"
            )
            continue

        md = path.with_suffix(".md")
        if not md.exists():
            errors.append(f"{path}: missing companion {md.name}")
            continue

        if method.id in seen_ids:
            errors.append(
                f"{path}: duplicate id '{method.id}' (also defined in {seen_ids[method.id]})"
            )
            continue
        seen_ids[method.id] = path

    if errors:
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print(f"\n{len(errors)} validation error(s)", file=sys.stderr)
        return 1

    print(f"All {len(files)} method(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
