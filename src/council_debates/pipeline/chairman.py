"""Chairman prompt construction and final aggregation call."""

from __future__ import annotations

import json
from typing import Any

from council_debates.core.models import ChairmanConfig, RankingResult, RoleResponse
from council_debates.providers.chat_completions import LLMClientProtocol


def build_chairman_prompt(
    user_prompt: str,
    role_responses: list[RoleResponse],
    ranking: RankingResult | None = None,
) -> str:
    payload: dict[str, Any] = {
        "original_user_request": user_prompt,
        "role_responses": [response.model_dump() for response in role_responses],
    }
    if ranking is not None:
        payload["ranking"] = {
            "valid_json": ranking.valid_json,
            "rankings": [item.model_dump() for item in ranking.rankings],
            "raw": ranking.raw,
            "error": ranking.error,
        }
    return (
        "Prepare the final answer using the role responses. "
        "Prefer the strongest, most correct parts. Resolve contradictions. "
        "Return Markdown.\n\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


class Chairman:
    def __init__(self, config: ChairmanConfig, client: LLMClientProtocol):
        self.config = config
        self.client = client

    def finalize(
        self,
        user_prompt: str,
        role_responses: list[RoleResponse],
        ranking: RankingResult | None = None,
    ) -> str:
        return self.client.complete(
            provider_name=self.config.provider,
            model=self.config.model,
            system_prompt=self.config.system_prompt,
            user_prompt=build_chairman_prompt(user_prompt, role_responses, ranking),
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
