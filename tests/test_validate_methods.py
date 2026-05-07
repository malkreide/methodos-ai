import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
SCRIPT = REPO / "scripts" / "validate_methods.py"


def test_validates_all_methods_in_repo():
    res = subprocess.run([sys.executable, str(SCRIPT)], cwd=REPO, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr


def test_rejects_methods_with_invalid_id_field(tmp_path):
    bad = tmp_path / "methods"
    bad.mkdir()
    (bad / "lowercase.json").write_text(
        json.dumps(
            {
                "id": "lowercase",
                "name": "Bad",
                "category": "strategy",
                "use_case": "x" * 50,
                "strengths": ["a"],
                "weaknesses": ["b"],
                "complexity_score": 1,
                "estimated_duration": {"min_minutes": 5, "max_minutes": 10},
            }
        )
    )
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--methods-dir", str(bad)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert res.returncode != 0
    assert "lowercase" in res.stderr or "lowercase" in res.stdout


def test_rejects_filename_id_mismatch(tmp_path):
    bad = tmp_path / "methods"
    bad.mkdir()
    (bad / "SWOT.json").write_text(
        json.dumps(
            {
                "id": "SWOT2",
                "name": "Wrong",
                "category": "strategy",
                "use_case": "x" * 50,
                "strengths": ["a"],
                "weaknesses": ["b"],
                "complexity_score": 1,
                "estimated_duration": {"min_minutes": 5, "max_minutes": 10},
            }
        )
    )
    res = subprocess.run(
        [sys.executable, str(SCRIPT), "--methods-dir", str(bad)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert res.returncode != 0
    output = res.stdout + res.stderr
    assert "SWOT" in output and ("mismatch" in output.lower() or "must equal" in output.lower())
