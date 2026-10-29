# MergeSentry

Read-only AI code review in your terminal, before you merge.

[![CI](https://github.com/haarikaalla/mergesentry/actions/workflows/ci.yml/badge.svg)](https://github.com/haarikaalla/mergesentry/actions/workflows/ci.yml)

MergeSentry fetches a GitHub or GitLab branch comparison using a read-only
token, sends the complete supported text diff and commit messages to a chosen
LLM, and prints a second opinion. It never posts reviews or changes repository
state. The LLM verdict is advisory; it does not replace tests or human review.

## Why this matters

A review tool that silently drops files or mistakes `NOT_SAFE_TO_MERGE` for
`SAFE_TO_MERGE` is dangerous. MergeSentry now fails closed when the host omits
a patch, paginates a comparison, or the diff exceeds its review budget. It
also requires one exact, structured verdict line before displaying a green
result.

```text
Local branch + committed config
          │
          ▼
GitHub / GitLab read-only comparison
          │  complete patches? host limit? pagination?
          ▼
15,000-character review budget
          │  reject oversized changes rather than truncate
          ▼
Selected LLM endpoint
          │  one exact verdict + summary + recommendation?
          ▼
Terminal-only advisory report
```

## Why read-only

A write-capable Git token is unnecessary. MergeSentry calls comparison APIs
with GET requests and makes no write calls to the Git host. The comparison
text **does leave the Git host** for the LLM provider you configure. Use a
company-approved endpoint for private or regulated source code.

## Install

```bash
python -m pip install -e .
```

The repository includes the source package. A PyPI release, if used, should
be checked independently for its version and publisher.

## Setup

```bash
cd your-project
mergesentry init
```

You'll be asked for:
- Git host (`github` or `gitlab`)
- Repo, e.g. `myorg/myproject`
- Base branch to compare against (default `main`)
- LLM provider (`anthropic`, `openai`, or `custom` for an enterprise gateway)

This creates a `.mergesentry.yml` in your repo — safe to commit, contains
no secrets.

Then set your credentials as environment variables (never commit these):

```bash
export GIT_TOKEN=your_read_only_personal_access_token
export LLM_API_KEY=your_llm_api_key
```

### Getting a read-only token

**GitHub:** Settings → Developer settings → Personal access tokens →
Fine-grained tokens → grant **Contents: Read-only** on the repo, nothing else.

**GitLab:** Project → Settings → Access Tokens → role `Reporter`,
scope `read_api` only.

## Usage

```bash
mergesentry review
```

```
mergesentry — main → feature/my-branch
============================================================

This is an AI-generated review — use judgment, verify before acting.
Write access was never used: nothing was posted or changed on the remote.
```

## Using an enterprise LLM gateway (e.g. company-provisioned Claude/GPT)

Set `llm_provider: custom` and `llm_endpoint: https://your-company-gateway/...`
in `.mergesentry.yml` — mergesentry will POST to it using the standard
OpenAI chat/completions request shape. `LLM_API_KEY` still comes from your
environment, provisioned by your company, never hardcoded.

## Validation and limits

Run the offline tests and command smoke check:

```bash
python -m pip install -e '.[dev]'
python -m pytest -q
mergesentry --help
```

CI runs the same checks on Python 3.10 and 3.13. Unit tests mock host APIs;
they do not require tokens or send source code to an LLM.

MergeSentry rejects omitted binary/large patches, paginated comparisons,
GitHub's 300-file comparison boundary, GitLab timeouts, and diffs over 15,000
characters. Split large changes into smaller reviews. It does not perform
static analysis, prove code safety, or guarantee the LLM follows the prompt.
For production use, pair it with code review, automated tests, and your
organization's data-handling policy.

## What this does not do

- Does not post MR/PR comments
- Does not set commit statuses or labels
- Does not block or approve merges
- Does not modify anything in your repo or on the remote

The merge decision remains yours.
