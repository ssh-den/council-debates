"""Command line interface for council-debates."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer

from .core.config import ConfigError, load_config
from .pipeline import DebateRunner
from .presentation import render_markdown
from .templates import CONFIG_TEMPLATE, ENV_TEMPLATE

app = typer.Typer(help="Run modular debates between multiple LLM roles.", no_args_is_help=True)

ConfigOutputOption = Annotated[
    Path,
    typer.Option(
        Path("config.example.yaml"),
        "--output",
        "-o",
        help="Where to write the example YAML config.",
    ),
]
EnvOutputOption = Annotated[
    Path,
    typer.Option(
        Path(".env.example"),
        "--output",
        "-o",
        help="Where to write the example environment file.",
    ),
]
ForceOption = Annotated[
    bool,
    typer.Option(False, "--force", "-f", help="Overwrite the file if it exists."),
]
PromptArgument = Annotated[str | None, typer.Argument(None, help="Prompt text to debate.")]
PromptFileOption = Annotated[
    Path | None,
    typer.Option(None, "--file", "-f", help="Read prompt text from a file."),
]
ConfigPathOption = Annotated[
    Path,
    typer.Option(Path("config.yaml"), "--config", "-c", help="Path to YAML config."),
]
RunOutputOption = Annotated[
    Path | None,
    typer.Option(None, "--output", "-o", help="Write Markdown result to this file."),
]
VerboseOption = Annotated[
    bool,
    typer.Option(False, "--verbose", "-v", help="Show provider/model logging."),
]


@app.command("init-config")
def init_config(output: ConfigOutputOption, force: ForceOption) -> None:
    """Create an example YAML configuration file."""
    if output.exists() and not force:
        typer.secho(
            f"File already exists: {output}. Use --force to overwrite.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)
    output.write_text(CONFIG_TEMPLATE, encoding="utf-8")
    typer.echo(f"Wrote example config to {output}")


@app.command("init-env")
def init_env(output: EnvOutputOption, force: ForceOption) -> None:
    """Create an example environment file."""
    if output.exists() and not force:
        typer.secho(
            f"File already exists: {output}. Use --force to overwrite.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(1)
    output.write_text(ENV_TEMPLATE, encoding="utf-8")
    typer.echo(f"Wrote example environment file to {output}")


@app.command("run")
def run(
    prompt: PromptArgument = None,
    prompt_file: PromptFileOption = None,
    config_path: ConfigPathOption = Path("config.yaml"),
    output: RunOutputOption = None,
    verbose: VerboseOption = False,
) -> None:
    """Run the full LLM debate pipeline and print Markdown."""
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    if prompt and prompt_file:
        typer.secho(
            "Use either a prompt argument or --file, not both.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)
    if prompt_file:
        if not prompt_file.exists():
            typer.secho(f"Prompt file not found: {prompt_file}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=2)
        user_prompt = prompt_file.read_text(encoding="utf-8")
    elif prompt:
        user_prompt = prompt
    else:
        typer.secho("Provide prompt text or --file prompt.txt.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)

    try:
        config = load_config(config_path)
        result = DebateRunner(config).run(user_prompt)
        markdown = render_markdown(
            result,
            include_role_responses=config.output.include_role_responses,
            include_ranking=config.output.include_ranking,
        )
    except ConfigError as exc:
        typer.secho(f"Configuration error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    except Exception as exc:
        typer.secho(f"Debate failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    if output:
        output.write_text(markdown, encoding="utf-8")
        typer.echo(f"Wrote result to {output}")
    typer.echo(markdown)


if __name__ == "__main__":
    app()
