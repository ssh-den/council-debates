# council-debates

Run multiple independent LLM roles against the same prompt, optionally rank their responses, and generate a final answer through a chairman model.

`council-debates` is a small modular Python 3.11+ package for running debates between independent LLM roles through OpenAI-compatible APIs.

The pipeline is deliberately strict:

1. Each role is called separately with only its own `system_prompt` and the original user prompt.
2. *(Optional)* A separate ranking LLM receives the original prompt plus all role responses.
3. A final chairman LLM receives the original prompt, role responses, and the optional ranking result, then writes the final Markdown answer.

You can omit the `ranking` block entirely. In that case the chairman aggregates role responses without an external ranker, which prevents the ranker from biasing the chairman's decision.

The package supports OpenAI, OpenRouter, LM Studio, Ollama OpenAI-compatible endpoint, vLLM, LocalAI, and any `/v1/chat/completions`-compatible provider.

## Pipeline

```text
User Prompt
     │
     ▼
┌───────────────┐
│ Role: Judge   │
├───────────────┤
│ Role: Skeptic │
├───────────────┤
│ Role: Builder │
└───────────────┘
     │
     ▼
┌────────────────────┐
│ Ranking (optional) │
└────────────────────┘
     │
     ▼
┌────────────────────┐
│ Chairman           │
└────────────────────┘
     │
     ▼
Final Markdown Answer
```

## Project layout

```text
council_debates/
├── CHANGELOG.md
├── pyproject.toml
├── README.md
├── config.example.yaml
├── .env.example
├── requirements-dev.txt
├── tests/
└── src/
    └── council_debates/
        ├── __init__.py
        ├── __main__.py
        ├── cli.py
        ├── core/
        ├── pipeline/
        ├── presentation/
        ├── providers/
        └── templates.py
```

## Install

From the project directory:

```bash
pip install council-debates
```

For development and tests:

```bash
.venv/bin/python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
```

Quality checks:

```bash
black --check .
ruff check .
mypy src tests
pylint src tests
pytest
```

## Create a config

```bash
council-debates init-config
council-debates init-env
cp .env.example .env
```

Edit `config.example.yaml` or save it as `config.yaml`. Set the environment variables referenced by `api_key_env`.

## Run

Prompt from the command line:

```bash
council-debates run "Suppose that a judge or magistrate..." --config config.yaml
```

Prompt from a file:

```bash
council-debates run --file prompt.txt --config config.yaml
```

Save Markdown output:

```bash
council-debates run "test prompt" --config config.yaml --output result.md
```

Show provider/model logging:

```bash
council-debates run "test prompt" --config config.yaml --verbose
```

## Configuration

All behavior is configured in YAML:

- `providers`: OpenAI-compatible base URLs and API keys or `api_key_env` references.
- `defaults`: default `temperature` and `max_tokens`.
- `roles`: independent debate roles; each role has its own provider, model, and system prompt.
- `ranking`: *(optional)* separate ranking model config. Omit it if you want the chairman to aggregate responses without external ranking.
- `chairman`: final aggregation model config.
- `output`: Markdown output options.

Example provider entries:

```yaml
providers:
  openai:
    base_url: "https://api.openai.com/v1"
    api_key_env: "OPENAI_API_KEY"
  openrouter:
    base_url: "https://openrouter.ai/api/v1"
    api_key_env: "OPENROUTER_API_KEY"
  local:
    base_url: "http://localhost:11434/v1"
    api_key: "ollama"
```

Local OpenAI-compatible servers usually accept any non-empty API key.

## Design Principle

Roles never see each other's responses.

Each role receives only:

- its own system prompt
- the original user prompt

This prevents early consensus, role contamination, and chain-of-thought leakage between participants.

## Contributions / Acknowledgments

The original idea of using multiple LLM roles in a council/debate setup comes from Andrej Karpathy's [`llm-council`](https://github.com/karpathy/llm-council/).
