"""Tests for the debate pipeline."""

from council_debates.core import (
    ChairmanConfig,
    DebateConfig,
    DefaultsConfig,
    ProviderConfig,
    RankingConfig,
    RoleConfig,
)
from council_debates.pipeline import DebateRunner


class FakeClient:
    def __init__(self):
        self.calls = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        model = kwargs["model"]
        if model == "ranker-model":
            return (
                '{"rankings":[{"rank":1,"role_id":"builder","score":9,'
                '"strengths":["practical"],"weaknesses":[],'
                '"reasoning":"most useful"}]}'
            )
        if model == "chair-model":
            return "# Final\nUse builder answer."
        return f"response from {model}"


def make_config():
    return DebateConfig(
        providers={
            "openai": ProviderConfig(base_url="https://api.openai.com/v1", api_key="test"),
            "local": ProviderConfig(base_url="http://localhost:11434/v1", api_key="ollama"),
        },
        defaults=DefaultsConfig(temperature=0.7, max_tokens=1000),
        roles=[
            RoleConfig(
                id="judge",
                name="Judge",
                provider="openai",
                model="judge-model",
                temperature=0.2,
                max_tokens=500,
                system_prompt="Judge prompt only",
            ),
            RoleConfig(
                id="builder",
                name="Builder",
                provider="local",
                model="builder-model",
                temperature=0.8,
                max_tokens=700,
                system_prompt="Builder prompt only",
            ),
        ],
        ranking=RankingConfig(
            provider="openai",
            model="ranker-model",
            temperature=0.1,
            max_tokens=600,
            system_prompt="Rank prompt only",
        ),
        chairman=ChairmanConfig(
            provider="openai",
            model="chair-model",
            temperature=0.3,
            max_tokens=800,
            system_prompt="Chair prompt only",
        ),
    )


def make_config_without_ranking():
    config = make_config()
    config.ranking = None
    return config


def test_debate_pipeline_calls_roles_ranking_and_chairman_in_order():
    fake = FakeClient()
    runner = DebateRunner(make_config(), client=fake)

    result = runner.run("User question")

    assert [call["model"] for call in fake.calls] == [
        "judge-model",
        "builder-model",
        "ranker-model",
        "chair-model",
    ]
    assert result.ranking is not None
    assert result.role_responses[0].content == "response from judge-model"
    assert result.role_responses[1].content == "response from builder-model"
    assert result.ranking.rankings[0].role_id == "builder"
    assert result.chairman_final_answer.startswith("# Final")


def test_debate_pipeline_skips_ranking_when_not_configured():
    fake = FakeClient()
    runner = DebateRunner(make_config_without_ranking(), client=fake)

    result = runner.run("User question")

    assert [call["model"] for call in fake.calls] == [
        "judge-model",
        "builder-model",
        "chair-model",
    ]
    assert result.ranking is None
    assert result.chairman_final_answer.startswith("# Final")


def test_each_role_gets_only_own_system_prompt_and_original_user_prompt():
    fake = FakeClient()
    runner = DebateRunner(make_config(), client=fake)

    runner.run("Original only")

    judge_call = fake.calls[0]
    builder_call = fake.calls[1]
    assert judge_call["system_prompt"] == "Judge prompt only"
    assert builder_call["system_prompt"] == "Builder prompt only"
    assert judge_call["user_prompt"] == "Original only"
    assert builder_call["user_prompt"] == "Original only"
    assert "Builder prompt" not in judge_call["system_prompt"]
    assert "Judge prompt" not in builder_call["system_prompt"]


def test_role_failure_is_captured_and_pipeline_continues():
    class PartlyFailingClient(FakeClient):
        def complete(self, **kwargs):
            if kwargs["model"] == "judge-model":
                raise RuntimeError("boom")
            return super().complete(**kwargs)

    fake = PartlyFailingClient()
    runner = DebateRunner(make_config(), client=fake)

    result = runner.run("Question")

    assert result.role_responses[0].error == "boom"
    assert result.role_responses[1].content == "response from builder-model"
    assert result.chairman_final_answer.startswith("# Final")
