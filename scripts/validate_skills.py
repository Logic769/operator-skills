#!/usr/bin/env python3
"""Validate every skill in skills/ against the repo rules.

Standard library only. Run from the repo root:
    python scripts/validate_skills.py

Checks:
- Each skill folder has a SKILL.md with YAML frontmatter.
- Frontmatter has `name` and `description`; name matches the folder and is kebab-case.
- Description is under 1024 characters and says when to use the skill.
- No em dashes in any text file.
- No obvious secrets in any file.
- Python scripts compile and import only the standard library.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
EM_DASH = "\u2014"
SECRET = re.compile(r"(sk-ant-[A-Za-z0-9_-]{20,}|\bsk-[A-Za-z0-9]{32,}|gh[pousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16})")
TEXT_SUFFIXES = {".md", ".py", ".json", ".csv", ".txt", ".yml", ".yaml"}
STDLIB = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}


def parse_frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    data = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def check_python(path: Path, errors: list[str]) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as e:
        errors.append(f"{path.relative_to(ROOT)}: syntax error: {e}")
        return
    if not STDLIB:
        return  # Python < 3.10 cannot list stdlib modules; skip the import check.
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = [node.module.split(".")[0]]
        for n in names:
            if n not in STDLIB:
                errors.append(f"{path.relative_to(ROOT)}: imports non-stdlib module `{n}`")


def main() -> int:
    errors: list[str] = []

    if not SKILLS.is_dir():
        print("error: skills/ folder not found", file=sys.stderr)
        return 2

    skill_dirs = sorted(p for p in SKILLS.iterdir() if p.is_dir())
    for d in skill_dirs:
        rel = d.relative_to(ROOT)
        skill_md = d / "SKILL.md"
        if not KEBAB.match(d.name):
            errors.append(f"{rel}: folder name must be kebab-case")
        if not skill_md.is_file():
            errors.append(f"{rel}: missing SKILL.md")
            continue
        fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        if fm is None:
            errors.append(f"{rel}/SKILL.md: missing or malformed frontmatter")
            continue
        if fm.get("name") != d.name:
            errors.append(f"{rel}/SKILL.md: name `{fm.get('name')}` must match folder `{d.name}`")
        desc = fm.get("description", "")
        if not desc:
            errors.append(f"{rel}/SKILL.md: description is required")
        elif len(desc) > 1024:
            errors.append(f"{rel}/SKILL.md: description over 1024 characters")
        elif "use when" not in desc.lower():
            errors.append(f"{rel}/SKILL.md: description should say when to use it ('Use when ...')")

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or path.suffix not in TEXT_SUFFIXES:
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        rel = path.relative_to(ROOT)
        if EM_DASH in text:
            errors.append(f"{rel}: contains an em dash; use a comma, colon or full stop")
        if SECRET.search(text):
            errors.append(f"{rel}: looks like it contains a secret")
        if path.suffix == ".py":
            check_python(path, errors)

    if errors:
        print(f"{len(errors)} problem(s):")
        for e in errors:
            print(f"- {e}")
        return 1
    print(f"OK: {len(skill_dirs)} skills passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
