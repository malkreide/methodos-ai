import pytest
from pydantic import ValidationError
from methodos.models import Method, Category, Duration

def _valid_payload(**overrides):
    base = dict(
        id="SWOT",
        name="SWOT Analysis",
        category="strategy",
        use_case="A structured framework for evaluating internal strengths and weaknesses against external opportunities and threats.",
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
        Method.model_validate(_valid_payload(id="swot"))   # lowercase start
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
        Method.model_validate(_valid_payload(
            estimated_duration={"min_minutes": 120, "max_minutes": 60}
        ))

def test_unknown_category_rejected():
    with pytest.raises(ValidationError):
        Method.model_validate(_valid_payload(category="dance"))

import json
import subprocess
import sys
from pathlib import Path

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
