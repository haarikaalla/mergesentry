# MergeSentry

Read-only AI code review, right in your terminal, before you merge.

Compares your feature branch against `main`/`develop` using a **read-only**
Personal Access Token (GitHub or GitLab — your choice), sends the diff to
an LLM of your choice (Claude, GPT, or any OpenAI-compatible enterprise
endpoint), and prints a plain-language safety verdict. Nothing is ever
written back to GitHub/GitLab — no comments, no labels, no status checks.
Just you, your terminal, and a second opinion before you open the MR.

## Why read-only

A write-capable token can post comments, change labels, or (if
misconfigured) worse. mergesentry never needs any of that — it only reads
diffs and prints to your terminal — so it only ever asks for the smallest
possible permission. Nothing it does can modify your repo or your remote.

## Install

```bash
pip install mergesentry
```

(Not on PyPI yet? Install locally from source: `pip install -e .` from
this project's root.)

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
git push origin feature/my-branch
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

## What this does NOT do

- Does not post MR/PR comments
- Does not set commit statuses or labels
- Does not block or approve merges
- Does not modify anything in your repo or on the remote

It's a second pair of eyes in your terminal — the decision is always yours.



``
View PyPI package-
 https://pypi.org/project/mergesentry/
