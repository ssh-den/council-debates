"""Tests for ranking prompt parsing and ranking calls."""

from council_debates.core import RankingConfig, RoleResponse
from council_debates.pipeline import RankingEngine, parse_ranking_json


class FakeClient:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        return self.text


def test_parse_ranking_json_from_plain_json():
    result = parse_ranking_json(
        '{"rankings":[{"rank":1,"role_id":"builder","score":9,'
        '"strengths":["clear"],"weaknesses":[],"reasoning":"best"}]}'
    )

    assert result.valid_json is True
    assert result.rankings[0].role_id == "builder"
    assert result.rankings[0].score == 9


def test_parse_ranking_json_from_text_with_fenced_json():
    raw = (
        "Here is the result:\n```json\n"
        '{"rankings":[{"rank":1,"role_id":"judge","score":8,'
        '"strengths":[],"weaknesses":[],"reasoning":"solid"}]}\n```'
    )

    result = parse_ranking_json(raw)

    assert result.valid_json is True
    assert result.rankings[0].role_id == "judge"


def test_parse_ranking_json_falls_back_to_raw_text():
    raw = "not json at all"

    result = parse_ranking_json(raw)

    assert result.valid_json is False
    assert result.raw == raw
    assert result.rankings == []
    assert result.error


def test_ranking_engine_calls_separate_ranking_model():
    fake = FakeClient('{"rankings":[]}')
    config = RankingConfig(
        provider="openai",
        model="rank-model",
        temperature=0.1,
        max_tokens=500,
        system_prompt="Rank only",
    )
    engine = RankingEngine(config, fake)

    result = engine.rank(
        "original prompt",
        [RoleResponse(role_id="judge", role_name="Judge", model="judge-model", content="answer")],
    )

    assert result.valid_json is True
    assert fake.calls[0]["provider_name"] == "openai"
    assert fake.calls[0]["model"] == "rank-model"
    assert fake.calls[0]["system_prompt"] == "Rank only"
    assert "original prompt" in fake.calls[0]["user_prompt"]
    assert "judge-model" in fake.calls[0]["user_prompt"]
