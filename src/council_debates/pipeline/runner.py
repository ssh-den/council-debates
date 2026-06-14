"""Main debate pipeline."""

from __future__ import annotations

import logging

from council_debates.core.models import (
    DebateConfig,
    DebateResult,
    RankingResult,
    RoleConfig,
    RoleResponse,
)
from council_debates.providers.chat_completions import ChatCompletionsClient, LLMClientProtocol

from .chairman import Chairman
from .ranking import RankingEngine

logger = logging.getLogger(__name__)


class DebateRunner:
    def __init__(self, config: DebateConfig, client: LLMClientProtocol | None = None):
        self.config = config
        self.client = client or ChatCompletionsClient(config.providers)

    def _run_role(self, role: RoleConfig, user_prompt: str) -> RoleResponse:
        logger.info(
            "Running role id=%s name=%s provider=%s model=%s",
            role.id,
            role.name,
            role.provider,
            role.model,
        )
        try:
            content = self.client.complete(
                provider_name=role.provider,
                model=role.model,
                system_prompt=role.system_prompt,
                user_prompt=user_prompt,
                temperature=role.temperature,
                max_tokens=role.max_tokens,
            )
            return RoleResponse(
                role_id=role.id,
                role_name=role.name,
                model=role.model,
                content=content,
            )
        except Exception as exc:
            logger.exception(
                "Role failed id=%s provider=%s model=%s",
                role.id,
                role.provider,
                role.model,
            )
            return RoleResponse(
                role_id=role.id,
                role_name=role.name,
                model=role.model,
                content="",
                error=str(exc),
            )

    def run(self, user_prompt: str) -> DebateResult:
        if not user_prompt.strip():
            raise ValueError("User prompt must not be empty.")

        role_responses = [self._run_role(role, user_prompt) for role in self.config.roles]

        ranking: RankingResult | None = None
        if self.config.ranking is not None:
            ranking = RankingEngine(self.config.ranking, self.client).rank(
                user_prompt,
                role_responses,
            )

        chairman_final_answer = ""
        chairman_error: str | None = None
        try:
            chairman_final_answer = Chairman(self.config.chairman, self.client).finalize(
                user_prompt,
                role_responses,
                ranking,
            )
        except Exception as exc:
            logger.exception("Chairman call failed")
            chairman_error = str(exc)
            chairman_final_answer = (
                "Chairman call failed. See the error section in the report; "
                "role responses and ranking data are still included."
            )

        return DebateResult(
            prompt=user_prompt,
            role_responses=role_responses,
            ranking=ranking,
            chairman_final_answer=chairman_final_answer,
            chairman_error=chairman_error,
        )
