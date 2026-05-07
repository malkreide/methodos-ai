"""Regenerate schemas/method_schema.json from the Pydantic Method model.

The Pydantic model is the single source of truth. Run after any change to
`src/methodos/models.py`. CI will fail if the committed schema drifts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from methodos.models import Method


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("schemas/method_schema.json"),
        help="Output path (default: schemas/method_schema.json)",
    )
    args = parser.parse_args()

    schema = Method.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://github.com/Malkreide/methodos-ai/blob/main/schemas/method_schema.json"
    schema["title"] = "Method"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(schema, indent=2, sort_keys=False) + "\n")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
