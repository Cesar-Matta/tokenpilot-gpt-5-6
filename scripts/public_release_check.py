"""Fast pre-publication scan for common credentials and private-machine traces."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IGNORED_DIRECTORIES = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
IGNORED_FILES = {Path(__file__).name}
PATTERNS = {
    "OpenAI-style key": r"\bsk-[A-Za-z0-9_-]{20,}\b",
    "Google API key": r"\bAIza[\w-]{20,}\b",
    "private key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "Windows user path": r"[A-Za-z]:\\Users\\",
    "Unix home path": r"/(?:home|Users)/[^/\\\s]+",
}


def should_scan(path: Path) -> bool:
    is_ignored_file = path.name in IGNORED_FILES
    has_ignored_directory = any(part in IGNORED_DIRECTORIES for part in path.parts)
    return not is_ignored_file and not has_ignored_directory


def main() -> None:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or not should_scan(path):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in PATTERNS.items():
            if re.search(pattern, content):
                findings.append(f"{label}: {path.relative_to(ROOT)}")
    if findings:
        raise SystemExit("Public-release check failed:\n" + "\n".join(findings))
    print("Public-release check passed")


if __name__ == "__main__":
    main()
