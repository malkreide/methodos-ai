from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from methodos.models import Context
from methodos.proposals import MAX_ISSUE_URL, issue_url, log_proposal, read_proposals

yaml = pytest.importorskip("yaml", reason="PyYAML parses the issue form")

ISSUE_FORM = Path(__file__).parents[1] / ".github" / "ISSUE_TEMPLATE" / "method-proposal.yml"


def _proposal(tmp_path, **overrides):
    kwargs = dict(
        name="Lean Coffee",
        problem="our meetings follow an agenda nobody asked for",
        description="Participants write topics, vote, and talk in timeboxes.",
        sources="Jim Benson, 2009",
        links=["https://leancoffee.org/"],
        contexts=[Context.EDUCATION],
        existing_method_id=None,
        similar_method_ids=["Liberating_Structures"],
        path=tmp_path / "p.jsonl",
    )
    kwargs.update(overrides)
    return log_proposal(**kwargs)


def _query(url: str) -> dict[str, str]:
    return {k: v[0] for k, v in parse_qs(urlsplit(url).query).items()}


def test_log_and_read_round_trip(tmp_path):
    ev = _proposal(tmp_path)
    assert len(ev.proposal_id) == 26
    (back,) = list(read_proposals(tmp_path / "p.jsonl"))
    assert back == ev


def test_read_skips_malformed_lines(tmp_path):
    path = tmp_path / "p.jsonl"
    _proposal(tmp_path)
    with path.open("a", encoding="utf-8") as f:
        f.write("{not json\n")
    assert len(list(read_proposals(path))) == 1


def test_issue_url_prefills_the_form(tmp_path):
    link = issue_url(_proposal(tmp_path), "owner/repo")
    assert link.omitted == []
    q = _query(link.url)
    assert q["template"] == "method-proposal.yml"
    assert q["title"] == "Method: Lean Coffee"
    assert q["contexts"] == "education"
    assert q["existing"] == "No, it is a new method"
    assert "Jim Benson, 2009" in q["sources"] and "- https://leancoffee.org/" in q["sources"]


def test_issue_url_names_the_existing_method(tmp_path):
    q = _query(issue_url(_proposal(tmp_path, existing_method_id="SWOT"), "o/r").url)
    assert q["name"] == "SWOT"
    assert q["existing"] == "Yes (name it above)"


def test_issue_url_keys_match_the_issue_form(tmp_path):
    """A renamed field id in the form would silently stop being prefilled."""
    form = yaml.safe_load(ISSUE_FORM.read_text(encoding="utf-8"))
    ids = {item["id"] for item in form["body"] if "id" in item}
    options = {
        item["id"]: item["attributes"].get("options") for item in form["body"] if "id" in item
    }
    q = _query(issue_url(_proposal(tmp_path), "o/r").url)
    assert set(q) - {"template", "title"} <= ids
    assert q["existing"] in options["existing"]
    assert set(options["contexts"]) == {c.value for c in Context}


def test_issue_url_drops_optional_fields_to_fit_githubs_limit(tmp_path):
    long = "ä" * 1500
    link = issue_url(_proposal(tmp_path, description=long, sources=long), "o/r")
    assert link.url is not None and len(link.url) <= MAX_ISSUE_URL
    assert "description" in link.omitted
    assert "problem" in _query(link.url)


# --- drafting -----------------------------------------------------------------

import json  # noqa: E402

from methodos.proposals import DRAFT_INPUT_CHARS, DraftError, draft_from_text  # noqa: E402
from tests.conftest import FakeLLM  # noqa: E402

_DRAFT = {
    "name": "Lean Coffee",
    "problem": "Sitzungen folgen einer Traktandenliste, die niemand gewünscht hat.",
    "description": "Alle notieren Themen, stimmen ab und besprechen sie in Zeitfenstern.",
    "sources": "Jim Benson, Jeremy Lightsmith (2009)",
    "contexts": ["education", "galaxy-brain"],
    "is_method": True,
    "note": None,
}


def test_draft_is_read_out_of_a_chatty_answer():
    llm = FakeLLM("Gern, hier der Entwurf:\n```json\n" + json.dumps(_DRAFT) + "\n```")
    draft = draft_from_text("Lean Coffee is a meeting format …", llm=llm, language="de")
    assert draft.name == "Lean Coffee"
    assert [c.value for c in draft.contexts] == ["education"], "unknown contexts are dropped"
    assert draft.is_method is True
    system, user = llm.calls[0]
    assert "German" in system
    assert "<<<DOCUMENT\nLean Coffee is a meeting format" in user


def test_draft_tolerates_wrong_types_field_by_field():
    llm = FakeLLM(json.dumps({"name": 3, "problem": "p", "sources": " ", "is_method": "no"}))
    draft = draft_from_text("text", llm=llm)
    assert draft.name == ""
    assert draft.problem == "p"
    assert draft.sources is None
    assert draft.is_method is True


def test_draft_without_json_is_an_error():
    with pytest.raises(DraftError):
        draft_from_text("text", llm=FakeLLM("I cannot help with that."))


def test_long_documents_are_cut_and_the_model_is_told():
    llm = FakeLLM(json.dumps(_DRAFT))
    draft_from_text("x" * (DRAFT_INPUT_CHARS + 500), llm=llm)
    _, user = llm.calls[0]
    assert "Only the beginning" in user
    assert user.count("x") <= DRAFT_INPUT_CHARS + 10


def test_document_text_cannot_inject_template_placeholders():
    llm = FakeLLM(json.dumps(_DRAFT))
    draft_from_text("weird {language} and {contexts} inside", llm=llm, language="de")
    _, user = llm.calls[0]
    assert "weird {language} and {contexts} inside" in user
