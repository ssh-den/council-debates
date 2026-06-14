"""Ranking prompt construction and JSON parsing."""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from council_debates.core.models import RankingConfig, RankingItem, RankingResult, RoleResponse
from council_debates.providers.chat_completions import LLMClientProtocol


def build_ranking_prompt(user_prompt: str, role_responses: list[RoleResponse]) -> str:
    payload = {
        "original_user_request": user_prompt,
        "role_responses": [response.model_dump() for response in role_responses],
        "required_output_format": {
            "rankings": [
                {
                    "rank": 1,
                    "role_id": "role id from input",
                    "score": 9,
                    "strengths": ["short strength"],
                    "weaknesses": ["short weakness"],
                    "reasoning": "Brief reason for this rank.",
                }
            ]
        },
    }
    return (
        "Rank the independent role responses. Do not write the final answer. "
        "Return valid JSON only, with no Markdown fences.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def _strip_code_fence(text: str) -> str:
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


def _extract_first_json_object(text: str) -> str | None:
    stripped_text = _strip_code_fence(text)
    start = stripped_text.find("{")
    if start == -1:
        return None

    depth = 0
    in_string = False
    escaped = False
    for idx in range(start, len(stripped_text)):
        char = stripped_text[idx]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return stripped_text[start : idx + 1]
    return None


def parse_ranking_json(raw: str) -> RankingResult:
    """Parse ranking JSON, extracting an object from Markdown/text when needed."""
    candidates: list[str] = [raw.strip(), _strip_code_fence(raw)]
    extracted = _extract_first_json_object(raw)
    if extracted:
        candidates.append(extracted)

    last_error: Exception | None = None
    for candidate in candidates:
        if not candidate:
            continue
        try:
            data: dict[str, Any] = json.loads(candidate)
            rankings = [RankingItem.model_validate(item) for item in data.get("rankings", [])]
            return RankingResult(raw=raw, valid_json=True, rankings=rankings)
        except (json.JSONDecodeError, TypeError, ValidationError) as exc:
            last_error = exc

    return RankingResult(
        raw=raw,
        valid_json=False,
        rankings=[],
        error=f"Could not parse ranking JSON: {last_error}",
    )


class RankingEngine:
    def __init__(self, config: RankingConfig, client: LLMClientProtocol):
        self.config = config
        self.client = client

    def rank(self, user_prompt: str, role_responses: list[RoleResponse]) -> RankingResult:
        try:
            raw = self.client.complete(
                provider_name=self.config.provider,
                model=self.config.model,
                system_prompt=self.config.system_prompt,
                user_prompt=build_ranking_prompt(user_prompt, role_responses),
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
        except Exception as exc:
            return RankingResult(
                raw="",
                valid_json=False,
                rankings=[],
                error=f"Ranking LLM call failed: {exc}",
            )
        return parse_ranking_json(raw)
