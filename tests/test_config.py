"""Tests for configuration loading and validation."""

from pathlib import Path

import pytest

from council_debates.core import ConfigError, MissingApiKeyError, load_config


def write_config(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(text, encoding="utf-8")
    return path


def test_load_config_resolves_env_keys_and_applies_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_OPENAI_KEY", "env-secret")
    path = write_config(
        tmp_path,
        """
providers:
  openai:
    base_url: "https://api.openai.com/v1"
    api_key_env: "TEST_OPENAI_KEY"
defaults:
  temperature: 0.42
  max_tokens: 777
roles:
  - id: judge
    name: Judge
    provider: openai
    model: gpt-test
    system_prompt: "Judge prompt"
ranking:
  provider: openai
  model: gpt-rank
  system_prompt: "Rank prompt"
chairman:
  provider: openai
  model: gpt-chair
  system_prompt: "Chair prompt"
""",
    )

    config = load_config(path)

    assert config.providers["openai"].api_key == "env-secret"
    assert config.roles[0].temperature == 0.42
    assert config.roles[0].max_tokens == 777
    assert config.ranking is not None
    assert config.ranking.temperature == 0.42
    assert config.ranking.max_tokens == 777
    assert config.chairman.temperature == 0.42
    assert config.chairman.max_tokens == 777


def test_load_config_can_read_dotenv_next_to_config(tmp_path, monkeypatch):
    monkeypatch.delenv("DOTENV_KEY", raising=False)
    (tmp_path / ".env").write_text("DOTENV_KEY=from-dotenv\n", encoding="utf-8")
    path = write_config(
        tmp_path,
        """
providers:
  local:
    base_url: "http://localhost:1234/v1"
    api_key_env: "DOTENV_KEY"
defaults:
  temperature: 0.1
  max_tokens: 100
roles:
  - id: builder
    name: Builder
    provider: local
    model: local-model
    system_prompt: "Build"
ranking:
  provider: local
  model: ranker
  system_prompt: "Rank"
chairman:
  provider: local
  model: chair
  system_prompt: "Chair"
""",
    )

    config = load_config(path)

    assert config.providers["local"].api_key == "from-dotenv"


def test_missing_api_key_is_reported_clearly(tmp_path, monkeypatch):
    monkeypatch.delenv("MISSING_TEST_KEY", raising=False)
    path = write_config(
        tmp_path,
        """
providers:
  openai:
    base_url: "https://api.openai.com/v1"
    api_key_env: "MISSING_TEST_KEY"
defaults:
  temperature: 0.1
  max_tokens: 100
roles:
  - id: judge
    name: Judge
    provider: openai
    model: gpt-test
    system_prompt: "Judge"
ranking:
  provider: openai
  model: ranker
  system_prompt: "Rank"
chairman:
  provider: openai
  model: chair
  system_prompt: "Chair"
""",
    )

    with pytest.raises(MissingApiKeyError, match="MISSING_TEST_KEY"):
        load_config(path)


def test_unknown_provider_reference_is_reported(tmp_path):
    path = write_config(
        tmp_path,
        """
providers:
  openai:
    base_url: "https://api.openai.com/v1"
    api_key: "test"
defaults:
  temperature: 0.1
  max_tokens: 100
roles:
  - id: judge
    name: Judge
    provider: missing
    model: gpt-test
    system_prompt: "Judge"
ranking:
  provider: openai
  model: ranker
  system_prompt: "Rank"
chairman:
  provider: openai
  model: chair
  system_prompt: "Chair"
""",
    )

    with pytest.raises(ConfigError, match="role 'judge'.*missing"):
        load_config(path)


def test_load_config_without_ranking_works(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_KEY", "secret")
    path = write_config(
        tmp_path,
        """
providers:
  openai:
    base_url: "https://api.openai.com/v1"
    api_key_env: "TEST_KEY"
defaults:
  temperature: 0.1
  max_tokens: 100
roles:
  - id: judge
    name: Judge
    provider: openai
    model: gpt-test
    system_prompt: "Judge"
chairman:
  provider: openai
  model: chair
  system_prompt: "Chair"
""",
    )

    config = load_config(path)

    assert config.ranking is None
    assert config.roles[0].temperature == 0.1
    assert config.chairman.temperature == 0.1
