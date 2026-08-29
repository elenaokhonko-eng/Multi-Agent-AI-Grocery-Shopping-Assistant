#!/usr/bin/env python3
"""
Security and Secret Scanner for CI.
Scans source files and configuration templates for unmasked credentials, active API keys,
private keys, and sensitive financial data.
"""

import os
import re
import sys
from pathlib import Path

# Directories and extensions to ignore
IGNORE_DIRS = {
    ".git", ".venv", "venv", "node_modules", "dist", "build",
    ".pytest_cache", ".ruff_cache", "__pycache__", "alembic",
}

IGNORE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".svg", ".ico", ".gif",
    ".pyc", ".db", ".sqlite", ".sqlite3", ".lock", ".log",
}

IGNORE_FILES = {
    "package-lock.json", "scan_secrets.py", ".env", ".env.local",
}

# Regex patterns for genuine leaked secrets (excluding documentation & placeholders)
SECRET_PATTERNS = [
    # Active MongoDB URI with actual password (excluding <username>, <password>, your_...)
    (re.compile(r"mongodb(?:\+srv)?://(?!<)[^:@\s]+:(?!<|your_password|password)[^@\s]{4,}@", re.IGNORECASE), "Exposed live MongoDB URI with credentials"),
    # Live Groq API key
    (re.compile(r"\bgsk_[a-zA-Z0-9]{35,}\b"), "Exposed Groq API key"),
    # Live OpenAI / Anthropic key
    (re.compile(r"\bsk-[a-zA-Z0-9]{35,}\b"), "Exposed API key"),
    # Private RSA/SSH Keys
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "Exposed Private Key"),
    # Hardcoded card numbers (16 digits in code/data files, not markdown)
    (re.compile(r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"), "Potential live Credit Card number"),
]


def scan_file(file_path: Path) -> list[tuple[int, str, str]]:
    findings = []
    # Skip documentation files from raw card word heuristics
    is_markdown = file_path.suffix.lower() == ".md"

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, start=1):
                # Skip markdown docs for generic token patterns
                if is_markdown and not ("mongodb" in line or "sk-" in line or "PRIVATE KEY" in line):
                    continue

                for pattern, description in SECRET_PATTERNS:
                    # Don't check card number regex in markdown text
                    if is_markdown and "Credit Card" in description:
                        continue

                    match = pattern.search(line)
                    if match:
                        matched_str = match.group(0)
                        # Filter out common safe documentation keywords
                        if any(safe in matched_str.lower() for safe in ["<username>", "<password>", "your_", "dummy", "test", "token", "placeholder"]):
                            continue
                        findings.append((line_no, description, line.strip()))
    except Exception as e:
        print(f"Warning: could not scan {file_path}: {e}", file=sys.stderr)

    return findings


def main():
    root_dir = Path(__file__).resolve().parent.parent
    total_findings = 0

    print(f"Scanning repository for leaked secrets and credentials at: {root_dir}")

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if file in IGNORE_FILES:
                continue

            file_path = Path(root) / file
            if file_path.suffix.lower() in IGNORE_EXTENSIONS:
                continue

            rel_path = file_path.relative_to(root_dir)
            findings = scan_file(file_path)

            if findings:
                for line_no, desc, line_content in findings:
                    print(f"[FAIL] {rel_path}:{line_no} - {desc}", file=sys.stderr)
                    print(f"    Line: {line_content[:100]}", file=sys.stderr)
                    total_findings += 1

    if total_findings > 0:
        print(f"\nScan failed: Found {total_findings} potential secret(s).", file=sys.stderr)
        sys.exit(1)
    else:
        print("[PASS] Secret scan passed: 0 credentials or leaked tokens detected.")
        sys.exit(0)


if __name__ == "__main__":
    main()
