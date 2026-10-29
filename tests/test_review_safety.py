from types import SimpleNamespace
from unittest.mock import patch

import pytest

from mergesentry.analyzer import MAX_DIFF_CHARS, ReviewInputError, build_prompt
from mergesentry.git_host import GitHubClient, GitLabClient, IncompleteDiffError
from mergesentry.reporter import parse_verdict, print_verdict

GOOD = "VERDICT: SAFE_TO_MERGE\nSUMMARY: Small change.\nCONCERNS:\n- None\nRECOMMENDATION: Verify tests."


def response(payload, links=None):
    return SimpleNamespace(json=lambda: payload, links=links or {}, raise_for_status=lambda: None)


def test_verdict_parser_accepts_only_exact_single_verdict(capsys):
    assert parse_verdict(GOOD) == "SAFE_TO_MERGE"
    assert parse_verdict(GOOD.replace("SAFE_TO_MERGE", "NEEDS_CHANGES")) == "NEEDS_CHANGES"
    for malformed in (
        GOOD.replace("SAFE_TO_MERGE", "NOT_SAFE_TO_MERGE"),
        GOOD + "\nVERDICT: NEEDS_CHANGES",
        "VERDICT: SAFE_TO_MERGE",
    ):
        with pytest.raises(ValueError):
            print_verdict(malformed, "main", "feature")
    assert capsys.readouterr().out == ""


def test_large_diff_is_rejected_before_llm_call():
    with pytest.raises(ReviewInputError, match="no partial diff was sent"):
        build_prompt("x" * (MAX_DIFF_CHARS + 1), [], "main", "feature")


def test_github_rejects_missing_patch_and_pagination():
    config = SimpleNamespace(repo="org/repo", api_base="https://api.github.com", git_token="test")
    client = GitHubClient(config)
    with (
        patch("mergesentry.git_host.requests.get", return_value=response({"files": [{"filename": "binary.dat"}], "commits": []})),
        pytest.raises(IncompleteDiffError, match="omitted patches"),
    ):
        client.compare("main", "feature")
    complete = {"files": [{"filename": "a.py", "patch": "+print(1)"}], "commits": [], "ahead_by": 0}
    with (
        patch("mergesentry.git_host.requests.get", return_value=response(complete, {"next": {"url": "next"}})),
        pytest.raises(IncompleteDiffError, match="paginated"),
    ):
        client.compare("main", "feature")


def test_github_complete_diff_and_encoded_refs():
    config = SimpleNamespace(repo="org/repo", api_base="https://api.github.com", git_token="test")
    payload = {"files": [{"filename": "a.py", "patch": "+print(1)"}], "commits": [{"commit": {"message": "Add print"}}], "ahead_by": 1}
    with patch("mergesentry.git_host.requests.get", return_value=response(payload)) as get:
        result = GitHubClient(config).compare("main", "feature/new")
    assert "+print(1)" in result["diff"]
    assert result["commits"] == ["Add print"]
    assert "feature%2Fnew" in get.call_args.args[0]


def test_gitlab_rejects_timed_out_comparison():
    config = SimpleNamespace(repo="org/repo", api_base="https://gitlab.com/api/v4", git_token="test")
    with (
        patch("mergesentry.git_host.requests.get", return_value=response({"compare_timeout": True, "diffs": []})),
        pytest.raises(IncompleteDiffError, match="timed out"),
    ):
        GitLabClient(config).compare("main", "feature")
