"""Tests that CLI bootstrap templates stay synchronized with repo examples."""

from pathlib import Path

from council_debates.templates import CONFIG_TEMPLATE, ENV_TEMPLATE

REPO_ROOT = Path(__file__).resolve().parent.parent


def _normalized(text: str) -> str:
    return text.replace("\r\n", "\n").strip() + "\n"


def test_config_template_matches_example_file():
    example_text = (REPO_ROOT / "config.example.yaml").read_text(encoding="utf-8")

    assert _normalized(CONFIG_TEMPLATE) == _normalized(example_text)


def test_env_template_matches_example_file():
    example_text = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

    assert _normalized(ENV_TEMPLATE) == _normalized(example_text)
