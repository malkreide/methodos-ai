from methodos.prompts.loader import load_prompt, render_explain_prompt, split_system_user


def test_load_prompt_returns_text():
    text = load_prompt("explain")
    assert "SYSTEM:" in text and "USER:" in text


def test_render_explain_prompt_substitutes_query():
    rendered = render_explain_prompt(
        query="enter a new market",
        candidates=[
            {
                "name": "SWOT",
                "similarity": 0.87,
                "complexity_score": 2,
                "use_case": "evaluate strengths and weaknesses",
                "strengths": ["a", "b"],
                "weaknesses": ["c"],
                "duration_min": 60,
                "duration_max": 180,
            }
        ],
    )
    assert "enter a new market" in rendered
    assert "SWOT" in rendered
    assert "0.87" in rendered
    assert "60" in rendered and "180" in rendered


def test_split_into_system_and_user_sections():
    rendered = render_explain_prompt(
        query="x",
        candidates=[
            {
                "name": "Y",
                "similarity": 0.5,
                "complexity_score": 1,
                "use_case": "z",
                "strengths": ["a"],
                "weaknesses": ["b"],
                "duration_min": 5,
                "duration_max": 10,
            }
        ],
    )
    sys_part, user_part = split_system_user(rendered)
    assert "expert management consultant" in sys_part.lower()
    assert "x" in user_part


# --- rerank provenance -----------------------------------------------------


def _cand(name, similarity, rerank_score=None):
    return {
        "name": name,
        "similarity": similarity,
        "rerank_score": rerank_score,
        "complexity_score": 2,
        "use_case": "u",
        "strengths": ["s"],
        "weaknesses": ["w"],
        "duration_min": 5,
        "duration_max": 10,
    }


def test_prompt_says_semantic_similarity_when_not_reranked():
    out = render_explain_prompt(query="q", candidates=[_cand("A", 0.5)])
    assert "ranked by semantic similarity" in out
    assert "rerank" not in out.lower()


def test_prompt_declares_rerank_ordering_when_reranked():
    """The list is no longer in similarity order — the prompt must not claim it is.

    Reranking can put a lower-similarity method first, so telling the model the
    list is 'ranked by semantic similarity' invites it to undo the reranking.
    """
    out = render_explain_prompt(
        query="q",
        candidates=[_cand("A", 0.46, 7.1), _cand("B", 0.47, -8.1)],
    )
    assert "ranked by semantic similarity" not in out
    assert "cross-encoder" in out
    assert "rerank: +7.10" in out
    assert "rerank: -8.10" in out


def test_prompt_keeps_similarity_visible_after_reranking():
    """Both numbers reach the model, so it can see where they disagree."""
    out = render_explain_prompt(query="q", candidates=[_cand("A", 0.46, 7.1)])
    assert "similarity: 0.46" in out
