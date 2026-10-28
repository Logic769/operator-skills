---
name: n8n-workflow-review
description: Review an exported n8n workflow JSON for reliability, security and maintainability problems before it goes to production. Use when the user shares an n8n workflow file or asks to audit, review, harden or debug an n8n workflow.
---

# n8n workflow review

Most n8n failures in production come from the same short list: no error path, secrets pasted into nodes, unbounded loops, and webhooks anyone can call. This skill checks for all of them the same way every time.

## Steps

1. **Get the JSON.** In n8n: open the workflow, menu, Download. Or copy all nodes and paste into a file.

2. **Run the linter.**

   ```bash
   python scripts/lint_workflow.py workflow.json
   python scripts/lint_workflow.py workflow.json --format json   # machine-readable
   ```

   It prints findings grouped by severity (`high`, `medium`, `low`) with the node name for each.

3. **Review what the script cannot judge**, by reading the workflow:
   - Does the trigger match the job (schedule vs webhook vs polling)?
   - Are AI or HTTP calls inside loops that could run hundreds of times? Estimate cost per run.
   - Is the data shape between nodes fragile (deep expressions like `$json.data[0].items[3]`)?
   - Is there a clear owner and a description in workflow settings?

4. **Report** using the format below. Lead with anything `high`. For each finding give the node, the risk in one line and the exact fix.

## What the linter checks

| Check | Severity |
|---|---|
| Possible secret (API key, bearer token, password) hardcoded in node parameters | high |
| Webhook trigger with no authentication | high |
| No error workflow set and no Error Trigger node | medium |
| HTTP Request node without retry on fail | medium |
| Nodes still named with defaults ("HTTP Request1", "Code") | low |
| Disabled nodes left in the workflow | low |
| Code nodes longer than 80 lines (move to a sub-workflow or service) | low |
| Workflow has no description / notes | low |

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
