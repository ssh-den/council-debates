"""YAML configuration loading and validation."""

from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import ValidationError

from .models import DebateConfig


class ConfigError(ValueError):
    """Raised when the YAML config is invalid or internally inconsistent."""


class MissingApiKeyError(ConfigError):
    """Raised when a provider has no api_key and its api_key_env is not set."""


class ProviderNotFoundError(ConfigError):
    """Raised when a role/ranking/chairman references a missing provider."""


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("Config YAML must contain a mapping at the top level.")
    return data


def _apply_defaults(data: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(data)
    defaults = result.get("defaults") or {}
    default_temperature = defaults.get("temperature", 0.7)
    default_max_tokens = defaults.get("max_tokens", 1200)

    for role in result.get("roles") or []:
        role.setdefault("temperature", default_temperature)
        role.setdefault("max_tokens", default_max_tokens)

    if isinstance(result.get("ranking"), dict):
        result["ranking"].setdefault("temperature", default_temperature)
        result["ranking"].setdefault("max_tokens", default_max_tokens)

    if isinstance(result.get("chairman"), dict):
        result["chairman"].setdefault("temperature", default_temperature)
        result["chairman"].setdefault("max_tokens", default_max_tokens)

    return result


def _load_dotenv_files(config_path: Path) -> None:
    # The shell environment always wins. Then we resolve .env in the current
    # directory and finally .env next to the config file.
    load_dotenv(dotenv_path=Path.cwd() / ".env", override=False)
    load_dotenv(dotenv_path=config_path.parent / ".env", override=False)


def _resolve_provider_keys(config: DebateConfig) -> None:
    for name, provider in config.providers.items():
        if provider.api_key:
            continue
        if provider.api_key_env:
            value = os.getenv(provider.api_key_env)
            if value:
                provider.api_key = value
                continue
            raise MissingApiKeyError(
                f"Missing API key for provider '{name}'. Set environment variable "
                f"{provider.api_key_env!r} or define api_key in the config."
            )
        raise MissingApiKeyError(
            f"Missing API key for provider '{name}'. Define api_key or api_key_env."
        )


def _validate_provider_references(config: DebateConfig) -> None:
    provider_names = set(config.providers)
    for role in config.roles:
        if role.provider not in provider_names:
            raise ProviderNotFoundError(
                f"Provider referenced by role '{role.id}' not found: {role.provider!r}"
            )
    if config.ranking and config.ranking.provider not in provider_names:
        raise ProviderNotFoundError(
            f"Provider referenced by ranking not found: {config.ranking.provider!r}"
        )
    if config.chairman.provider not in provider_names:
        raise ProviderNotFoundError(
            f"Provider referenced by chairman not found: {config.chairman.provider!r}"
        )

    seen_role_ids: set[str] = set()
    for role in config.roles:
        if role.id in seen_role_ids:
            raise ConfigError(f"Duplicate role id found: {role.id!r}")
        seen_role_ids.add(role.id)


def load_config(path: str | Path) -> DebateConfig:
    """Load, validate, and normalize a YAML config file."""
    config_path = Path(path).expanduser().resolve()
    _load_dotenv_files(config_path)
    data = _apply_defaults(_read_yaml(config_path))
    try:
        config = DebateConfig.model_validate(data)
    except ValidationError as exc:
        raise ConfigError(f"Invalid config structure: {exc}") from exc
    _validate_provider_references(config)
    _resolve_provider_keys(config)
    return config
