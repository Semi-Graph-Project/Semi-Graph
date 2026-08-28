from semigraph.agent.prompts import SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT


def test_synthesis_prompt_locks_the_answer_style():
    prompt = SYNTHESIZE_ATTEMPTS_SYSTEM_PROMPT

    assert "**Answer**" in prompt
    assert "**Key evidence**" in prompt
    assert "**Evidence gap**" in prompt
    assert "Use 1-5 flat bullets" in prompt
    assert "Do not add other headings" in prompt
    assert (
        'Do not begin with phrases such as "Based on the provided evidence"'
        in prompt
    )
