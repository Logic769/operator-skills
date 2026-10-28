#!/usr/bin/env python3
"""Lint an exported n8n workflow JSON for common production problems.

Standard library only. Python 3.9+.

Usage:
    python lint_workflow.py workflow.json [--format text|json]

Exit code is 1 when any high-severity finding exists, else 0.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

SECRET_PATTERNS = [
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"), "OpenAI-style secret key"),
    (re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"), "Anthropic API key"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"), "GitHub token"),
    (re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}"), "Slack token"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]{20,}"), "Bearer token"),
]
SECRET_KEY_NAMES = re.compile(r"(?i)(api[_-]?key|secret|password|token|authorization)")
DEFAULT_NAME = re.compile(
    r"^(HTTP Request|Code|Function|Set|Edit Fields|IF|If|Switch|Merge|Webhook|"
    r"Schedule Trigger|Split In Batches|Loop Over Items|No Operation, do nothing)\d*$"
)
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def walk(value, path=""):
    """Yield (path, string_value) for every string inside nested params."""
    if isinstance(value, dict):
        for k, v in value.items():
            yield from walk(v, f"{path}.{k}" if path else k)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(value, str):
        yield path, value


def find_secrets(node):
    params = node.get("parameters", {})
    hits = []
    for path, text in walk(params):
        if text.startswith("={{") or "$credentials" in text:
            continue  # expressions are fine
        for pattern, label in SECRET_PATTERNS:
            if pattern.search(text):
                hits.append(f"{label} in `{path}`")
                break
    # header/query pairs like {"name": "x-api-key", "value": "abc123..."}
    for path, text in walk(params):
        if path.endswith(".name") and SECRET_KEY_NAMES.search(text):
            value_path = path[: -len(".name")] + ".value"
            value = dict(walk(params)).get(value_path, "")
            if value and not value.startswith("=") and len(value) >= 12:
                hits.append(f"literal value for `{text}`")
    return sorted(set(hits))


def lint(workflow: dict) -> list[dict]:
    findings = []
    nodes = workflow.get("nodes", [])
    settings = workflow.get("settings", {}) or {}

    def add(sev, node, msg):
        findings.append({"severity": sev, "node": node, "message": msg})

    types = [n.get("type", "") for n in nodes]
    if not settings.get("errorWorkflow") and not any("errorTrigger" in t for t in types):
        add("medium", None, "No error workflow set and no Error Trigger node. Failures will be silent.")

    if not (workflow.get("meta", {}) or {}).get("description") and not any(
        "stickyNote" in t for t in types
    ):
        add("low", None, "No description or sticky note explaining what this workflow does.")

    for n in nodes:
        name = n.get("name", "?")
        ntype = n.get("type", "")
        params = n.get("parameters", {}) or {}

        if "stickyNote" in ntype:
            continue

        for hit in find_secrets(n):
            add("high", name, f"Possible hardcoded secret: {hit}. Move it to an n8n credential.")

        if ntype.endswith(".webhook"):
            auth = params.get("authentication", "none")
            if auth in ("none", None, ""):
                add("high", name, "Webhook has no authentication. Anyone with the URL can trigger it.")

        if ntype.endswith(".httpRequest") and not n.get("retryOnFail"):
            add("medium", name, "HTTP Request without Retry On Fail. Transient errors will stop the run.")

        if n.get("disabled"):
            add("low", name, "Disabled node left in the workflow. Remove it or document why.")

        if DEFAULT_NAME.match(name):
            add("low", name, "Default node name. Rename it to describe what it does.")

        if ntype.endswith(".code") or ntype.endswith(".function"):
            code = params.get("jsCode") or params.get("functionCode") or params.get("pythonCode") or ""
            lines = code.count("\n") + 1 if code else 0
            if lines > 80:
                add("low", name, f"Code node is {lines} lines. Consider a sub-workflow or external service.")

    findings.sort(key=lambda f: (SEVERITY_ORDER[f["severity"]], f["node"] or ""))
    return findings


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("workflow")
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args(argv)

    try:
        with open(args.workflow, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"error: file not found: {args.workflow}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"error: not valid JSON ({e})", file=sys.stderr)
        return 2

    # Accept a single workflow, a list of workflows, or a bare {"nodes": [...]} paste.
    workflows = data if isinstance(data, list) else [data]
    any_high = False
    output = []
    for wf in workflows:
        findings = lint(wf)
        any_high |= any(f["severity"] == "high" for f in findings)
        output.append({"name": wf.get("name", "(unnamed)"), "nodes": len(wf.get("nodes", [])), "findings": findings})

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
