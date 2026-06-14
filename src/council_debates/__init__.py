"""Council Debates package."""

from importlib.metadata import PackageNotFoundError, version

from .core import (
    ChairmanConfig,
    ConfigError,
    DebateConfig,
    DebateResult,
    DefaultsConfig,
    MissingApiKeyError,
    OutputConfig,
    ProviderConfig,
    ProviderNotFoundError,
    RankingConfig,
    RankingItem,
    RankingResult,
    RoleConfig,
    RoleResponse,
    load_config,
)
from .pipeline import DebateRunner
from .presentation import render_markdown

__all__ = [
    "ChairmanConfig",
    "ConfigError",
    "DebateConfig",
    "DebateResult",
    "DebateRunner",
    "DefaultsConfig",
    "MissingApiKeyError",
    "OutputConfig",
    "ProviderConfig",
    "ProviderNotFoundError",
    "RankingConfig",
    "RankingItem",
    "RankingResult",
    "RoleConfig",
    "RoleResponse",
    "load_config",
    "render_markdown",
]

try:
    __version__ = version("council-debates")
except PackageNotFoundError:
    __version__ = "0.1.0"
