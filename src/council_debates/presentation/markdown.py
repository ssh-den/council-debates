"""Markdown rendering for debate results."""

from __future__ import annotations

from council_debates.core.models import DebateResult


def _escape_table_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ").strip()


def render_markdown(
    result: DebateResult,
    *,
    include_role_responses: bool = True,
    include_ranking: bool = True,
) -> str:
    lines: list[str] = ["# LLM Debate Result", "", "## Prompt", "", result.prompt.strip(), ""]

    if include_role_responses:
        lines.extend(["## Role Responses", ""])
        for response in result.role_responses:
            lines.extend(
                [
                    f"### {response.role_name}",
                    "",
                    f"- Role ID: `{response.role_id}`",
                    f"- Model: `{response.model}`",
                ]
            )
            if response.error:
                lines.extend(
                    [
                        f"- Error: `{response.error}`",
                        "",
                        response.content or "_No response content._",
                        "",
                    ]
                )
            else:
                lines.extend(["", response.content.strip() or "_No response content._", ""])

    if include_ranking and result.ranking is not None:
        lines.extend(["## Ranking", ""])
        if result.ranking.rankings:
            lines.extend(["| Rank | Role | Score | Reason |", "|---:|---|---:|---|"])
            for item in sorted(result.ranking.rankings, key=lambda ranking: ranking.rank):
                lines.append(
                    "| "
                    f"{_escape_table_cell(item.rank)} | "
                    f"{_escape_table_cell(item.role_id)} | "
                    f"{_escape_table_cell(item.score)} | "
                    f"{_escape_table_cell(item.reasoning)} |"
                )
            lines.append("")
        else:
            if result.ranking.error:
                lines.extend([f"_Ranking unavailable: {result.ranking.error}_", ""])
            if result.ranking.raw:
                lines.extend(["```", result.ranking.raw.strip(), "```", ""])
            else:
                lines.append("")

    lines.extend(["## Chairman Final Answer", "", result.chairman_final_answer.strip(), ""])
    if result.chairman_error:
        lines.extend(["## Chairman Error", "", f"`{result.chairman_error}`", ""])

    return "\n".join(lines).rstrip() + "\n"
