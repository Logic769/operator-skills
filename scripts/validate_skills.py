#!/usr/bin/env python3
"""Validate every skill in skills/ against the repo rules.

Standard library only. Python 3.9+. Run from anywhere:
    python3 scripts/validate_skills.py

Checks:
- Each skill folder has a SKILL.md with YAML frontmatter.
- `name` matches the folder, is lowercase-hyphen, at most 64 characters, and
  does not contain the reserved words "anthropic" or "claude".
- `description` exists, is at most 1024 characters, has no angle brackets, says
  when to use the skill, and is safe as an unquoted YAML value.
- Scripts referenced from SKILL.md via ${CLAUDE_SKILL_DIR} exist.
- No em dashes in any text file.
- No obvious secrets in any file.
- Python scripts compile and import only the standard library (Python 3.10+;
  on 3.9 the import check is skipped because the stdlib list is unavailable).

Exit codes: 0 all good, 1 problems found, 2 repo layout error.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RESERVED = ("anthropic", "claude")
EM_DASH = "\u2014"
SECRET = re.compile(
    r"(sk-ant-[A-Za-z0-9_-]{20,}|\bsk-[A-Za-z0-9]{32,}|gh[pousr]_[A-Za-z0-9]{30,}"
    r"|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)
SCRIPT_REF = re.compile(r"\$\{CLAUDE_SKILL_DIR\}/([\w./-]+)")
TEXT_SUFFIXES = {".md", ".py", ".json", ".csv", ".txt", ".yml", ".yaml"}
HAS_STDLIB_LIST = hasattr(sys, "stdlib_module_names")
STDLIB = set(getattr(sys, "stdlib_module_names", ())) | {"__future__"}
SELF = Path(__file__).resolve()


def parse_frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    data = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith((" ", "\t", "#")):
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()
    return data


def unquote(v: str) -> tuple[str, bool]:
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1], True
    return v, False


def check_skill(d: Path, errors: list[str]) -> None:
    rel = d.relative_to(ROOT)
    skill_md = d / "SKILL.md"
    if not KEBAB.match(d.name):
        errors.append(f"{rel}: folder name must be lowercase-hyphen")
    if not skill_md.is_file():
        errors.append(f"{rel}: missing SKILL.md")
        return
    text = skill_md.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    if fm is None:
        errors.append(f"{rel}/SKILL.md: missing or malformed frontmatter")
        return

    name, _ = unquote(fm.get("name", ""))
    if name != d.name:
        errors.append(f"{rel}/SKILL.md: name `{name}` must match folder `{d.name}`")
    if len(name) > 64:
        errors.append(f"{rel}/SKILL.md: name longer than 64 characters")
    if any(word in name for word in RESERVED):
        errors.append(f"{rel}/SKILL.md: name must not contain {' or '.join(RESERVED)}")

    raw_desc = fm.get("description", "")
    desc, quoted = unquote(raw_desc)
    if not desc:
        errors.append(f"{rel}/SKILL.md: description is required")
    else:
        if len(desc) > 1024:
            errors.append(f"{rel}/SKILL.md: description over 1024 characters")
        if "<" in desc or ">" in desc:
            errors.append(f"{rel}/SKILL.md: description must not contain < or >")
        if "use when" not in desc.lower():
            errors.append(f"{rel}/SKILL.md: description should say when to use it ('Use when ...')")
        if not quoted and (": " in desc or " #" in desc or desc[0] in "[{&*!|>%@`"):
            errors.append(
                f"{rel}/SKILL.md: description has characters that break unquoted YAML "
                "(': ', ' #' or a leading special character); wrap it in quotes"
            )

    for ref in SCRIPT_REF.findall(text):
        if not (d / ref).exists():
            errors.append(f"{rel}/SKILL.md: references missing file ${{CLAUDE_SKILL_DIR}}/{ref}")


def check_python(path: Path, errors: list[str]) -> None:
    rel = path.relative_to(ROOT)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as e:
        errors.append(f"{rel}: syntax error: {e}")
        return
    if not HAS_STDLIB_LIST:
        return
    local_modules = {p.stem for p in path.parent.glob("*.py")}
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name.split(".")[0] for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names = [node.module.split(".")[0]]
        for n in names:
            if n not in STDLIB and n not in local_modules:
                errors.append(f"{rel}: imports non-stdlib module `{n}`")


def main() -> int:
    errors: list[str] = []
    if not SKILLS.is_dir():
        print("error: skills/ folder not found", file=sys.stderr)
        return 2

    skill_dirs = sorted(p for p in SKILLS.iterdir() if p.is_dir())
    for d in skill_dirs:
        check_skill(d, errors)

    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".git" in path.parts or path.suffix not in TEXT_SUFFIXES:
            continue
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8", errors="replace")
        if EM_DASH in text:
            errors.append(f"{rel}: contains an em dash; use a comma, colon or full stop")
        if path.resolve() != SELF and SECRET.search(text):
            errors.append(f"{rel}: looks like it contains a secret")
        if path.suffix == ".py":
            check_python(path, errors)

    if errors:
        print(f"{len(errors)} problem(s):")
        for e in errors:
            print(f"- {e}")
        return 1
    note = "" if HAS_STDLIB_LIST else " (import check skipped on Python < 3.10)"
    print(f"OK: {len(skill_dirs)} skills passed{note}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
