---
name: n8n-workflow-review
description: Review an exported n8n workflow JSON for reliability, security and maintainability problems before it goes to production. Use when the user shares an n8n workflow file or asks to audit, review, harden or debug an n8n workflow.
---

# n8n workflow review

Common n8n production problems include missing error handling, secrets pasted into nodes, loops that run far more often than expected, and webhooks anyone can call. This skill checks for them the same way every time.

## Steps

1. **Get the JSON.** In n8n: open the workflow, menu, Download. Or copy all nodes and paste into a file.

2. **Run the linter.**

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/lint_workflow.py workflow.json
   python3 ${CLAUDE_SKILL_DIR}/scripts/lint_workflow.py workflow.json --format json
   ```

   `${CLAUDE_SKILL_DIR}` is this skill's folder (Claude Code fills it in). Where it is not set, use the path to `scripts/lint_workflow.py` next to this SKILL.md.

   It prints findings grouped by severity (`high`, `medium`, `low`) with the node name for each. Exit codes: `0` no high findings, `1` at least one high finding, `2` the file is not a readable n8n workflow. The script only reads the file; it never runs anything from it.

3. **Review what the script cannot judge**, by reading the workflow:
   - Does the trigger match the job (schedule vs webhook vs polling)?
   - Are AI or HTTP calls inside loops that could run hundreds of times? Estimate cost per run.
   - Is the data shape between nodes fragile (deep expressions like `$json.data[0].items[3]`)?
   - Is there a clear owner and a description in workflow settings?

4. **Report** using the format below. Lead with anything `high`. For each finding give the node, the risk in one line and the exact fix.

## What the linter checks

| Check | Severity |
|---|---|
| Possible hardcoded secret: known token formats (Anthropic, OpenAI, GitHub, Slack, AWS, Google, Bearer), header and query values named like keys, and `api_key`-style pairs inside JSON bodies or code | high |
| Webhook, Form or Chat trigger with no authentication | high |
| No error workflow set and no Error Trigger node | medium |
| HTTP Request node without retry on fail | medium |
| Nodes still named with defaults ("HTTP Request1", "Code") | low |
| Disabled nodes left in the workflow | low |
| Code nodes longer than 80 lines (move to a sub-workflow or service) | low |
| Workflow has no description / notes | low |

The secret check is a safety net, not a guarantee. It skips values written as n8n expressions (`={{ ... }}`), so also skim those by eye.

## Output format

```
n8n review: "Daily lead sync" (14 nodes)
Verdict: fix 2 high issues before activating.

HIGH
- [Fetch Apollo] API key in header value. Move it to a credential.
- [Inbound Webhook] No auth. Set Header Auth or Basic Auth.

MEDIUM
- No error workflow. Settings > Error workflow > pick your alert workflow.

LOW
- 5 nodes use default names. Rename to what they do.

Cost note: the OpenAI node runs once per lead inside a loop (about 300 calls per day).
```
