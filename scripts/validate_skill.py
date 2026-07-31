"""Validate the repository-bundled Codex skill without external dependencies."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "tokenpilot-router"


def main() -> None:
    skill_md = SKILL / "SKILL.md"
    content = skill_md.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise SystemExit("SKILL.md must begin with YAML frontmatter")
    _, frontmatter, _ = content.split("---", 2)
    metadata = yaml.safe_load(frontmatter)
    if metadata.get("name") != "tokenpilot-router" or not metadata.get("description"):
        raise SystemExit("SKILL.md needs a valid name and description")
    interface = yaml.safe_load((SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8"))
    default_prompt = interface.get("interface", {}).get("default_prompt", "")
    if "$tokenpilot-router" not in default_prompt:
        raise SystemExit("agents/openai.yaml must include a matching default prompt")
    print("Skill validation passed")


if __name__ == "__main__":
    main()
