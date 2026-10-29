"""
Read-only clients for GitHub and GitLab.

Both classes expose the same interface: get_current_branch() and
compare(base, head) -> {"diff": str, "commits": [str]}

Only GET requests are ever made. No write scope is required or used.
"""
import subprocess
from urllib.parse import quote

import requests


class IncompleteDiffError(ValueError):
    """The host did not return a complete text diff."""


def _require_complete_patches(files, patch_key, response, *, limit=None):
    if response.links.get("next") or (limit is not None and len(files) >= limit):
        raise IncompleteDiffError("Comparison is paginated or exceeds the host file limit; split the change.")
    missing = [item.get("filename") or item.get("new_path") or "<unknown>"
               for item in files if not item.get(patch_key)]
    if missing:
        raise IncompleteDiffError(
            "Host omitted patches for: " + ", ".join(missing[:5])
            + (" ..." if len(missing) > 5 else "")
        )


def get_current_branch():
    """Read the current branch from local git — no API call needed."""
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"]
    ).decode().strip()


class GitHubClient:
    def __init__(self, config):
        self.repo = config.repo  # "org/name"
        self.base_url = config.api_base
        self.headers = {
            "Authorization": f"Bearer {config.git_token}",
            "Accept": "application/vnd.github+json",
        }

    def compare(self, base, head):
        # GitHub's compare endpoint: read-only, no write scope needed
        url = f"{self.base_url}/repos/{self.repo}/compare/{quote(base, safe='')}...{quote(head, safe='')}"
        resp = requests.get(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        files = data.get("files", [])
        _require_complete_patches(files, "patch", resp, limit=300)
        if len(data.get("commits", [])) < data.get("ahead_by", 0):
            raise IncompleteDiffError("Host omitted commit messages; split the change.")

        diff_text = ""
        for f in files:
            diff_text += f"\n--- {f['filename']} ---\n"
            diff_text += f["patch"] + "\n"

        commits = [c["commit"]["message"] for c in data.get("commits", [])]
        return {"diff": diff_text, "commits": commits}


class GitLabClient:
    def __init__(self, config):
        self.project_id = config.repo  # can be "org/name" (URL-encoded) or numeric ID
        self.base_url = config.api_base
        self.headers = {"PRIVATE-TOKEN": config.git_token}

    def compare(self, base, head):
        import urllib.parse
        project = urllib.parse.quote(self.project_id, safe="")
        url = f"{self.base_url}/projects/{project}/repository/compare"
        resp = requests.get(
            url, headers=self.headers, params={"from": base, "to": head}, timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("compare_timeout") or data.get("overflow"):
            raise IncompleteDiffError("GitLab comparison timed out or overflowed; split the change.")
        diffs = data.get("diffs", [])
        _require_complete_patches(diffs, "diff", resp)

        diff_text = ""
        for d in diffs:
            diff_text += f"\n--- {d.get('new_path', d.get('old_path'))} ---\n"
            diff_text += d["diff"] + "\n"

        commits = [c["message"] for c in data.get("commits", [])]
        return {"diff": diff_text, "commits": commits}


def get_client(config):
    if config.host == "github":
        return GitHubClient(config)
    elif config.host == "gitlab":
        return GitLabClient(config)
    raise ValueError(f"Unsupported host: {config.host}")
