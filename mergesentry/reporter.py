"""Formats the LLM verdict for clean terminal output."""
import re

GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def parse_verdict(verdict_text):
    """Accept only one exact verdict line; malformed model output fails closed."""
    lines = re.findall(r"^VERDICT:.*$", verdict_text, re.MULTILINE)
    if len(lines) != 1:
        raise ValueError("Model response has no single valid VERDICT line; review it manually.")
    matches = re.fullmatch(r"VERDICT:\s*(SAFE_TO_MERGE|NEEDS_CHANGES)\s*", lines[0])
    if matches is None:
        raise ValueError("Model response has an invalid VERDICT line; review it manually.")
    if not re.search(r"^SUMMARY:\s*\S", verdict_text, re.MULTILINE):
        raise ValueError("Model response lacks a summary; review it manually.")
    if not re.search(r"^RECOMMENDATION:\s*\S", verdict_text, re.MULTILINE):
        raise ValueError("Model response lacks a recommendation; review it manually.")
    return matches.group(1)


def print_verdict(verdict_text, base, head):
    is_safe = parse_verdict(verdict_text) == "SAFE_TO_MERGE"
    color = GREEN if is_safe else YELLOW
    icon = "✅" if is_safe else "⚠️"

    print()
    print(f"{BOLD}mergesentry{RESET} — {base} → {head}")
    print("=" * 60)
    print(f"{color}{icon}  {verdict_text.strip()}{RESET}")
    print("=" * 60)
    print()

    print("This is an AI-generated review — use judgment, verify before acting.")
    print("Write access was never used: nothing was posted or changed on the remote.\n")
