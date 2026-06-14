"""Tests for Markdown rendering."""

from council_debates.core import DebateResult, RankingItem, RankingResult, RoleResponse
from council_debates.presentation import render_markdown


def test_render_markdown_includes_prompt_roles_ranking_and_final_answer():
    result = DebateResult(
        prompt="What should we do?",
        role_responses=[
            RoleResponse(role_id="judge", role_name="Judge", model="gpt", content="Judge says no."),
            RoleResponse(
                role_id="skeptic",
                role_name="Skeptic",
                model="claude",
                content="",
                error="API failed",
            ),
        ],
        ranking=RankingResult(
            raw='{"rankings":[]}',
            valid_json=True,
            rankings=[
                RankingItem(
                    rank=1,
                    role_id="judge",
                    score=8,
                    strengths=["logical"],
                    weaknesses=["brief"],
                    reasoning="Best available.",
                )
            ],
        ),
        chairman_final_answer="Final answer here.",
    )

    markdown = render_markdown(result)

    assert "# LLM Debate Result" in markdown
    assert "## Prompt" in markdown
    assert "### Judge" in markdown
    assert "Judge says no." in markdown
    assert "API failed" in markdown
    assert "| 1 | judge | 8 | Best available. |" in markdown
    assert "## Chairman Final Answer" in markdown
    assert "Final answer here." in markdown
