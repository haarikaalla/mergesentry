"""Formats the LLM verdict for clean terminal output."""

GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_verdict(verdict_text, base, head):
    is_safe = "SAFE_TO_MERGE" in verdict_text.upper()
    color = GREEN if is_safe else YELLOW
    icon = "✅" if is_safe else "⚠️"

    print()
    print(f"{BOLD}mergesentry{RESET} — {base} → {head}")
    print("=" * 60)
    print(f"{color}{icon}  {verdict_text.strip()}{RESET}")
    print("=" * 60)
    print()

    if not is_safe:
        print("This is an AI-generated review — use judgment, verify before acting.")
        print("Write access was never used: nothing was posted or changed on the remote.\n")
