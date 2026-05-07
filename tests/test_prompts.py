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
