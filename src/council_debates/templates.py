"""Built-in text templates for bootstrap files.

Keep these constants synchronized with the repository root files
``config.example.yaml`` and ``.env.example``.
"""

from __future__ import annotations

CONFIG_TEMPLATE = """providers:
  openai:
    base_url: "https://api.openai.com/v1"
    api_key_env: "OPENAI_API_KEY"

  openrouter:
    base_url: "https://openrouter.ai/api/v1"
    api_key_env: "OPENROUTER_API_KEY"

  local:
    base_url: "http://localhost:11434/v1"
    api_key: "ollama"

defaults:
  temperature: 0.7
  max_tokens: 1200

roles:
  - id: "judge"
    name: "Judge"
    provider: "openai"
    model: "gpt-4o-mini"
    temperature: 0.2
    max_tokens: 1200
    system_prompt: |
      You are a strict judge.

      Evaluate the user's request with emphasis on logic, consistency,
      evidence, trade-offs, and risks.

      Identify which arguments are well supported, which are weak or
      speculative, and what conclusions are justified.

      Be precise, critical, and concise.

  - id: "skeptic"
    name: "Skeptic"
    provider: "openrouter"
    model: "anthropic/claude-3.5-sonnet"
    temperature: 0.5
    max_tokens: 1200
    system_prompt: |
      You are a skeptical reviewer.

      Find weak assumptions, missing context, contradictions, blind spots, and hidden risks.

      Challenge ideas constructively and suggest alternative interpretations when appropriate.

      Do not produce the final answer. Focus on critique and analysis.

  - id: "builder"
    name: "Builder"
    provider: "local"
    model: "qwen2.5:14b"
    temperature: 0.8
    max_tokens: 1200
    system_prompt: |
      You are a constructive solution builder.

      Focus on practical implementation, clear structure, actionable
      recommendations, and useful next steps.

      Prefer concrete solutions over abstract discussion.

      Do not critique unless it helps improve the solution.

ranking:
  provider: "openai"
  model: "gpt-4o-mini"
  temperature: 0.1
  max_tokens: 1500
  system_prompt: |
    You are a neutral ranking engine.

    You receive the original user request and multiple independent role responses.

    Rank the responses by usefulness, correctness, completeness, and practical value.

    Return only valid JSON.

    Do not include Markdown, code fences, comments, or explanatory text outside the JSON document.

    Use the following schema:

    {
      "rankings": [
        {
          "rank": 1,
          "role_id": "string",
          "score": 0-10,
          "strengths": ["string"],
          "weaknesses": ["string"],
          "reasoning": "string"
        }
      ]
    }

chairman:
  provider: "openrouter"
  model: "qwen/qwen-2.5-72b-instruct"
  temperature: 0.3
  max_tokens: 2000
  system_prompt: |
    You are the chairman of the debate.

    You receive the original user request, all role responses, and optionally a ranking result.

    Produce the final answer in Markdown.

    Use the strongest insights from the role responses, resolve
    contradictions, remove weak arguments, and synthesize a coherent
    final response.

    Treat the ranking result as advisory rather than authoritative.

    If a role provides a stronger argument than its ranking suggests, use your own judgment.

    Do not mention the debate process unless it improves the answer.

output:
  format: "markdown"
  include_role_responses: true
  include_ranking: true
"""

ENV_TEMPLATE = """# Copy this file to .env and set the keys needed by your config.yaml.
OPENAI_API_KEY="sk-..."
OPENROUTER_API_KEY="sk-or-..."

# Local providers such as Ollama, LM Studio, vLLM, and LocalAI often accept any non-empty key.
# Example:
# LOCAL_API_KEY="ollama"
"""
