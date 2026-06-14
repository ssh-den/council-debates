"""Pydantic models used by the LLM debate pipeline."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_url: str
    api_key_env: str | None = None
    api_key: str | None = Field(default=None, repr=False)

    @field_validator("base_url")
    @classmethod
    def base_url_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("base_url must not be empty")
        return value.rstrip("/")


class DefaultsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    temperature: float = 0.7
    max_tokens: int = 1200


class RoleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 1200
    system_prompt: str

    @field_validator("id", "name", "provider", "model", "system_prompt")
    @classmethod
    def required_text_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value


class RankingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 1200
    system_prompt: str

    @field_validator("provider", "model", "system_prompt")
    @classmethod
    def required_text_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value


class ChairmanConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 1200
    system_prompt: str

    @field_validator("provider", "model", "system_prompt")
    @classmethod
    def required_text_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be empty")
        return value


class OutputConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    format: Literal["markdown"] = "markdown"
    include_role_responses: bool = True
    include_ranking: bool = True


class DebateConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    providers: dict[str, ProviderConfig]
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    roles: list[RoleConfig] = Field(min_length=1)
    ranking: RankingConfig | None = None
    chairman: ChairmanConfig
    output: OutputConfig = Field(default_factory=OutputConfig)


class RoleResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role_id: str
    role_name: str
    model: str
    content: str = ""
    error: str | None = None


class RankingItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    rank: int
    role_id: str
    score: float | int | None = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    reasoning: str = ""


class RankingResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    raw: str
    valid_json: bool
    rankings: list[RankingItem] = Field(default_factory=list)
    error: str | None = None


class DebateResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str
    role_responses: list[RoleResponse]
    ranking: RankingResult | None = None
    chairman_final_answer: str
    chairman_error: str | None = None
