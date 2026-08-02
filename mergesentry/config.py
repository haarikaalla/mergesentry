"""
Configuration loader for mergesentry.

Reads settings from .mergesentry.yml (committed to repo, no secrets)
and credentials from environment variables (never committed).
"""
import os
import sys
import yaml
from pathlib import Path


DEFAULT_CONFIG_PATH = ".mergesentry.yml"


class ConfigError(Exception):
    pass


class Config:
    def __init__(self, path=DEFAULT_CONFIG_PATH):
        if not Path(path).exists():
            raise ConfigError(
                f"No {path} found. Run `mergesentry init` first."
            )

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        # --- repo host settings (from committed config file) ---
        self.host = data.get("host")  # "github" or "gitlab"
        if self.host not in ("github", "gitlab"):
            raise ConfigError(
                "host must be 'github' or 'gitlab' in .mergesentry.yml"
            )

        self.repo = data.get("repo")  # e.g. "myorg/myproject"
        if not self.repo:
            raise ConfigError("repo (e.g. 'org/name') missing in .mergesentry.yml")

        self.base_branch = data.get("base_branch", "main")
        self.api_base = data.get(
            "api_base",
            "https://api.github.com" if self.host == "github" else "https://gitlab.com/api/v4",
        )

        # --- LLM provider settings (from committed config file) ---
        self.llm_provider = data.get("llm_provider", "anthropic")  # anthropic | openai | custom
        self.llm_model = data.get("llm_model", self._default_model())
        self.llm_endpoint = data.get("llm_endpoint")  # only needed for provider: custom

        # --- credentials (env vars only, NEVER stored in the yml) ---
        self.git_token = self._require_env(
            "GIT_TOKEN",
            "Read-only Personal Access Token for GitHub/GitLab. "
            "Export it with: export GIT_TOKEN=your_token_here",
        )
        self.llm_key = self._require_env(
            "LLM_API_KEY",
            "API key for your LLM provider (Anthropic/OpenAI/etc). "
            "Export it with: export LLM_API_KEY=your_key_here",
        )

    def _default_model(self):
        return {
            "anthropic": "claude-haiku-4-5-20251001",
            "openai": "gpt-4o-mini",
        }.get(self.llm_provider, "claude-haiku-4-5-20251001")

    @staticmethod
    def _require_env(name, help_text):
        value = os.environ.get(name)
        if not value:
            print(f"\nMissing required environment variable: {name}", file=sys.stderr)
            print(help_text, file=sys.stderr)
            sys.exit(1)
        return value
