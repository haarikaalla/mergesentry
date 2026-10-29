"""
mergesentry CLI

Commands:
  mergesentry init      Create a .mergesentry.yml config in the current repo
  mergesentry review    Compare current branch vs base branch, print AI verdict
"""
import sys

import click
import requests

from .analyzer import analyze
from .config import DEFAULT_CONFIG_PATH, Config, ConfigError
from .git_host import get_client, get_current_branch
from .reporter import print_verdict


@click.group()
def cli():
    """mergesentry — read-only AI review for your branch before you merge."""


@cli.command()
def init():
    """Interactively create a .mergesentry.yml in the current directory."""
    from pathlib import Path

    import yaml

    if Path(DEFAULT_CONFIG_PATH).exists():
        click.echo(f"{DEFAULT_CONFIG_PATH} already exists. Delete it first to re-init.")
        sys.exit(1)

    host = click.prompt("Git host", type=click.Choice(["github", "gitlab"]))
    repo = click.prompt("Repo (e.g. 'myorg/myproject')")
    base_branch = click.prompt("Base branch to compare against", default="main")
    llm_provider = click.prompt(
        "LLM provider", type=click.Choice(["anthropic", "openai", "custom"]), default="anthropic"
    )

    config_data = {
        "host": host,
        "repo": repo,
        "base_branch": base_branch,
        "llm_provider": llm_provider,
    }

    if llm_provider == "custom":
        config_data["llm_endpoint"] = click.prompt("Enterprise LLM endpoint URL")

    with open(DEFAULT_CONFIG_PATH, "w") as f:
        yaml.dump(config_data, f, default_flow_style=False)

    click.echo(f"\nCreated {DEFAULT_CONFIG_PATH}. Commit this file — it has no secrets.")
    click.echo("\nBefore running `mergesentry review`, set these environment variables:")
    click.echo("  export GIT_TOKEN=your_read_only_personal_access_token")
    click.echo("  export LLM_API_KEY=your_llm_api_key")


@cli.command()
@click.option("--head", default=None, help="Branch to review (defaults to current branch)")
def review(head):
    """Compare current branch against base branch and print an AI safety verdict."""
    try:
        config = Config()
    except ConfigError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    head_branch = head or get_current_branch()

    click.echo(f"Fetching diff: {config.base_branch} vs {head_branch} (read-only)...")
    client = get_client(config)

    try:
        result = client.compare(config.base_branch, head_branch)
    except (requests.RequestException, ValueError, KeyError, TypeError) as e:
        click.echo(f"Failed to fetch diff from {config.host}: {e}", err=True)
        sys.exit(1)

    if not result["diff"].strip():
        click.echo("No differences found — nothing to review.")
        return

    click.echo(f"Sending diff to {config.llm_provider} ({config.llm_model})...")
    try:
        verdict = analyze(config, result["diff"], result["commits"], config.base_branch, head_branch)
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as e:
        click.echo(f"LLM call failed: {e}", err=True)
        sys.exit(1)

    try:
        print_verdict(verdict, config.base_branch, head_branch)
    except ValueError as e:
        click.echo(f"Review incomplete: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
