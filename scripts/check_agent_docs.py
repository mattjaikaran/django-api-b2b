#!/usr/bin/env python3
"""Check the agent context files.

AGENTS.md is the single source of agent instructions, so it must exist and every
relative link in it must resolve. CLAUDE.md may only import it.

Fails when:
  missing   AGENTS.md is absent at the repo root or empty.
  link      a relative link in AGENTS.md or CLAUDE.md does not resolve.
  claude    CLAUDE.md holds prose or rules instead of only `@AGENTS.md` imports.

Usage:
    python3 scripts/check_agent_docs.py

Exit: 0 pass, 1 a check failed. No dependencies, no database.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "AGENTS.md"
CLAUDE = ROOT / "CLAUDE.md"

# Links inside code spans and fenced blocks are examples, not links.
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
CODE_SPAN_RE = re.compile(r"`[^`\n]*`")
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def link_targets(text: str) -> list[str]:
    """Return the targets of the inline Markdown links in `text`."""
    body = FENCE_RE.sub("", text)
    body = CODE_SPAN_RE.sub("", body)
    targets: list[str] = []
    for raw in LINK_RE.findall(body):
        target = raw.strip()
        if target.startswith("<"):
            target = target[1:].split(">", 1)[0]
        else:
            target = target.split()[0] if target else ""
        targets.append(target)
    return targets


def is_relative(target: str) -> bool:
    """A local path, not a URL, an anchor or an absolute path."""
    return bool(target) and not target.startswith(("#", "/")) and not urlsplit(target).scheme


def check_links(path: Path) -> list[str]:
    problems: list[str] = []
    for target in link_targets(path.read_text(encoding="utf-8")):
        if not is_relative(target):
            continue
        relative = unquote(target.split("#", 1)[0])
        if not relative:
            continue
        resolved = (path.parent / relative).resolve()
        if not resolved.is_relative_to(ROOT) or not resolved.exists():
            problems.append(f"{path.name}: link does not resolve: {target}")
    return problems


def check_agents() -> list[str]:
    if not AGENTS.is_file():
        return ["AGENTS.md is missing at the repo root"]
    if not AGENTS.read_text(encoding="utf-8").strip():
        return ["AGENTS.md is empty"]
    return check_links(AGENTS)


def check_claude() -> list[str]:
    if not CLAUDE.is_file():
        return []
    problems = [
        f"CLAUDE.md: rule text must live in AGENTS.md, not CLAUDE.md: {line.strip()!r}"
        for line in CLAUDE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("@")
    ]
    return problems + check_links(CLAUDE)


def main() -> int:
    problems = check_agents() + check_claude()
    print(f"  {'FAIL' if problems else 'ok  '}  agent docs")
    for problem in problems:
        print(f"  {problem}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
