#!/usr/bin/env python3
"""Lint an exported n8n workflow JSON for common production problems.

Standard library only. Python 3.9+. Reads only the given file, makes no
network calls, never executes anything from the workflow.

Usage:
    python3 lint_workflow.py workflow.json [--format text|json]

Exit codes:
    0  no high-severity findings
    1  at least one high-severity finding
    2  input error (missing file, invalid JSON, not an n8n workflow)
"""
from __future__ import annotations

import argparse
import json
import re
import sys

# Order matters: more specific patterns first.
SECRET_PATTERNS = [
    (re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"), "Anthropic API key"),
    (re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}"), "OpenAI-style secret key"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"), "GitHub token"),
    (re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key"),
    (re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), "Google API key"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{20,}=*"), "Bearer token"),
]
SECRET_KEY_NAMES = re.compile(r"(?i)(api[_-]?key|secret|password|passwd|token|authorization|auth)")
# "key": "value" pairs inside JSON bodies and code, e.g. {"api_key": "abc..."}
INLINE_SECRET = re.compile(
    r"""(?ix)["']?(api[_-]?key|secret|password|passwd|access[_-]?token|auth[_-]?token)["']?
        \s*[:=]\s*["']([^"'\s]{12,})["']"""
)
PUBLIC_TRIGGERS = (".webhook", ".formTrigger", ".chatTrigger")
DEFAULT_NAME = re.compile(
    r"^(HTTP Request|Code|Function|Set|Edit Fields|IF|If|Switch|Merge|Webhook|"
    r"Schedule Trigger|Split In Batches|Loop Over Items|No Operation, do nothing)\d*$"
)
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}
MAX_DEPTH = 200


class InputError(Exception):
    """Input is not something we can lint."""


def walk(value, path="", depth=0):
    """Yield (path, string_value) for every string inside nested params."""
    if depth > MAX_DEPTH:
        return
    if isinstance(value, dict):
        for k, v in value.items():
            yield from walk(v, f"{path}.{k}" if path else str(k), depth + 1)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, f"{path}[{i}]", depth + 1)
    elif isinstance(value, str):
        yield path, value


def as_dict(value) -> dict:
    return value if isinstance(value, dict) else {}


def find_secrets(params: dict) -> list[str]:
    hits: set[str] = set()
    strings = dict(walk(params))
    for path, text in strings.items():
        if "$credentials" in text:
            continue
        labelled = False
        for pattern, label in SECRET_PATTERNS:
            if pattern.search(text):
                hits.add(f"{label} in `{path}`")
                labelled = True
                break
        if not labelled:
            m = INLINE_SECRET.search(text)
            if m and not m.group(2).startswith(("{{", "$")):
                hits.add(f"literal `{m.group(1)}` value in `{path}`")
    # Header or query pairs like {"name": "x-api-key", "value": "abc123..."}.
    # Runs after the pattern pass so a value already flagged is not reported twice.
    for path, text in strings.items():
        if path.endswith(".name") and SECRET_KEY_NAMES.search(text):
            value_path = path[: -len(".name")] + ".value"
            value = strings.get(value_path, "")
            if value and not value.startswith("=") and len(value) >= 12:
                already = any(value_path in h for h in hits)
                if not already:
                    hits.add(f"literal value for `{text}` in `{value_path}`")
    return sorted(hits)


def lint(workflow: dict) -> list[dict]:
    findings = []
    nodes = workflow.get("nodes")
    if not isinstance(nodes, list):
        raise InputError("workflow has no `nodes` list; is this an n8n export?")
    nodes = [n for n in nodes if isinstance(n, dict)]
    settings = as_dict(workflow.get("settings"))
    meta = as_dict(workflow.get("meta"))

    def add(sev, node, msg):
        findings.append({"severity": sev, "node": node, "message": msg})

    types = [str(n.get("type") or "") for n in nodes]
    if not settings.get("errorWorkflow") and not any("errorTrigger" in t for t in types):
        add("medium", None, "No error workflow set and no Error Trigger node. Failures will be silent.")

    if not meta.get("description") and not any("stickyNote" in t for t in types):
        add("low", None, "No description or sticky note explaining what this workflow does.")

    for n in nodes:
        name = str(n.get("name") or "?")
        ntype = str(n.get("type") or "")
        params = as_dict(n.get("parameters"))

        if "stickyNote" in ntype:
            continue

        for hit in find_secrets(params):
            add("high", name, f"Possible hardcoded secret: {hit}. Move it to an n8n credential.")

        if ntype.endswith(PUBLIC_TRIGGERS):
            auth = params.get("authentication", "none")
            if auth in ("none", None, ""):
                add("high", name, "Public trigger has no authentication. Anyone with the URL can run it.")

        if ntype.endswith(".httpRequest") and not n.get("retryOnFail"):
            add("medium", name, "HTTP Request without Retry On Fail. Transient errors will stop the run.")

        if n.get("disabled") is True:
            add("low", name, "Disabled node left in the workflow. Remove it or document why.")

        if DEFAULT_NAME.match(name):
            add("low", name, "Default node name. Rename it to describe what it does.")

        if ntype.endswith((".code", ".function")):
            code = params.get("jsCode") or params.get("functionCode") or params.get("pythonCode")
            if isinstance(code, str) and code:
                lines = code.count("\n") + 1
                if lines > 80:
                    add("low", name, f"Code node is {lines} lines. Consider a sub-workflow or external service.")

    findings.sort(key=lambda f: (SEVERITY_ORDER[f["severity"]], f["node"] or ""))
    return findings


def load(path: str):
    try:
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise InputError(f"file not found: {path}")
    except IsADirectoryError:
        raise InputError(f"expected a file, got a directory: {path}")
    except UnicodeDecodeError:
        raise InputError("file is not UTF-8 text")
    except json.JSONDecodeError as e:
        raise InputError(f"not valid JSON ({e})")
    except RecursionError:
        raise InputError("JSON is nested too deeply")
    except OSError as e:
        raise InputError(f"could not read file ({e})")

    # Accept one workflow, a list of workflows, or a bare {"nodes": [...]} paste.
    workflows = data if isinstance(data, list) else [data]
    workflows = [w for w in workflows if isinstance(w, dict)]
    if not workflows:
        raise InputError("no n8n workflow objects found in the file")
    return workflows


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("workflow")
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args(argv)

    try:
        workflows = load(args.workflow)
        output = []
        for wf in workflows:
            findings = lint(wf)
            output.append({
                "name": str(wf.get("name") or "(unnamed)"),
                "nodes": len(wf.get("nodes") or []),
                "findings": findings,
            })
    except InputError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except RecursionError:
        print("error: workflow is nested too deeply", file=sys.stderr)
        return 2

    any_high = any(f["severity"] == "high" for wf in output for f in wf["findings"])

    if args.format == "json":
        print(json.dumps(output, indent=2))
    else:
        for wf in output:
            print(f'n8n review: "{wf["name"]}" ({wf["nodes"]} nodes)')
            if not wf["findings"]:
                print("No issues found by the linter.\n")
                continue
            for sev in ("high", "medium", "low"):
                items = [f for f in wf["findings"] if f["severity"] == sev]
                if items:
                    print(f"\n{sev.upper()}")
                    for f in items:
                        where = f"[{f['node']}] " if f["node"] else ""
                        print(f"- {where}{f['message']}")
            print()
    return 1 if any_high else 0


if __name__ == "__main__":
    sys.exit(main())
