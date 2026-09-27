import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from methodos.models import Category, Method


def _valid_payload(**overrides):
    base = dict(
        id="SWOT",
        name="SWOT Analysis",
        category="strategy",
        use_case=(
            "A structured framework for evaluating internal strengths and weaknesses "
            "against external opportunities and threats."
        ),
        strengths=["widely recognized", "simple to facilitate"],
        weaknesses=["can be superficial", "no prioritization"],
        complexity_score=2,
        estimated_duration={"min_minutes": 60, "max_minutes": 180},
        references=["https://en.wikipedia.org/wiki/SWOT_analysis"],
    )
    base.update(overrides)
    return base


def test_valid_method_round_trips():
    m = Method.model_validate(_valid_payload())
    assert m.id == "SWOT"
    assert m.category is Category.STRATEGY
    assert m.estimated_duration.min_minutes == 60
    assert m.doc_path == "methods/SWOT.md"


def test_id_must_be_pascal_or_snake_case_starting_capital():
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(id="swot"))  # lowercase start
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(id="2SWOT"))  # digit start


def test_use_case_minimum_length_enforced():
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(use_case="too short"))


def test_strengths_must_be_non_empty():
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(strengths=[]))


def test_strengths_capped_at_twelve():
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(strengths=[f"item {i}" for i in range(13)]))


def test_complexity_score_bounded_one_to_five():
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(complexity_score=0))
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(complexity_score=6))


def test_duration_max_must_be_ge_min():
    with pytest.raises(ValidationError):
        Method.model_validate(
            _valid_payload(estimated_duration={"min_minutes": 120, "max_minutes": 60})
        )


def test_unknown_category_rejected():
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(category="dance"))


def test_committed_schema_matches_pydantic_model(tmp_path):
    """Regenerating the schema should produce a byte-identical file."""
    repo_root = Path(__file__).parent.parent
    target = tmp_path / "method_schema.json"
    script = repo_root / "scripts" / "regenerate_schema.py"
    subprocess.check_call(
        [sys.executable, str(script), "--out", str(target)],
        cwd=repo_root,
    )
    committed = (repo_root / "schemas" / "method_schema.json").read_text()
    regenerated = target.read_text()
    assert committed == regenerated, "Run `make schema` to update the committed schema."


# --- optional metadata (schema additions that must stay non-breaking) --------


def test_new_metadata_is_optional_and_defaults_empty():
    m = Method.model_validate(_valid_payload())
    assert m.use_cases == [] and m.contexts == [] and m.formats == []
    assert m.language == "en"
    assert m.group_size is None and m.owner is None and m.last_reviewed is None


def test_every_shipped_method_still_validates():
    """The additions are optional, so no existing file needed touching."""
    root = Path(__file__).parent.parent / "methods"
    for f in root.glob("*.json"):
        Method.model_validate_json(f.read_text(encoding="utf-8"))


def test_full_metadata_round_trips():
    m = Method.model_validate(
        _valid_payload(
            use_cases=["A school leadership team reviewing its position before a new term."],
            contexts=["education", "public-sector"],
            formats=["in-person", "remote"],
            group_size={"min_people": 3, "max_people": 12},
            audience=["school leadership"],
            language="de",
            owner="Hayal Özkan",
            last_reviewed="2026-09-01",
            assets=[
                {"title": "Canvas", "kind": "template", "path": "canvas.pdf"},
                {
                    "title": "Facilitation kit",
                    "kind": "slides",
                    "access": "premium",
                    "url": "https://example.org/kit",
                },
            ],
        )
    )
    assert m.last_reviewed is not None and m.last_reviewed.isoformat() == "2026-09-01"
    assert [a.access.value for a in m.assets] == ["open", "premium"]


@pytest.mark.parametrize(
    "asset",
    [
        {"title": "t", "kind": "template"},  # neither location
        {"title": "t", "kind": "template", "path": "a.pdf", "url": "https://x.org/a"},  # both
        {"title": "t", "kind": "template", "access": "premium", "path": "a.pdf"},  # premium file
        {"title": "t", "kind": "template", "path": "../escape.pdf"},
        {"title": "t", "kind": "template", "path": "/etc/passwd"},
        {"title": "t", "kind": "template", "url": "http://insecure.org/a"},
    ],
)
def test_invalid_assets_are_rejected(asset):
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(assets=[asset]))


@pytest.mark.parametrize(
    "overrides",
    [
        {"contexts": ["education", "education"]},
        {"use_cases": ["short"]},
        {"use_cases": [_valid_payload()["use_case"]]},  # repeats the canonical one
        {"language": "deu"},
        {"group_size": {"min_people": 5, "max_people": 2}},
        {"contexts": ["school"]},
    ],
)
def test_invalid_metadata_is_rejected(overrides):
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(**overrides))
