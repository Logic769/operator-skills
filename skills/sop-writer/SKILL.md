---
name: sop-writer
description: Turn a messy description of how a task is done (notes, a voice transcript, a Loom summary, a chat thread) into a clear standard operating procedure. Use when the user asks to write, document, formalize or clean up an SOP, process, checklist or how-to for a recurring task.
---

# SOP writer

An SOP is good when a new hire can follow it on day one without asking anyone. Write for that person.

## Steps

1. **Extract from the source:** the trigger (what starts the task), the owner, tools used, every action, every decision point, and the finished state.
2. **List gaps** the source does not answer: who approves, what to do when something fails, how long it should take. Ask the user about the gaps that matter. If they are not available, mark each one `TBD: <question>` in the SOP instead of guessing.
3. **Write the SOP** using the format below.
4. **Point out automation.** Mark any step that is copy, paste, lookup or reformatting with `[automate?]` and add one line on how (n8n, Zapier, a script, a Claude skill).

## Format

```markdown
# SOP: <task name>

**Owner:** <role, not person>    **Frequency:** <daily/weekly/on trigger>    **Time:** <expected minutes>
**Trigger:** <what starts it>
**Done when:** <observable finished state>
**Tools:** <list with access needed>

## Steps
1. <Verb first. One action per step.>
   - Detail or exact field values, if needed.
2. If <condition>, go to step 5. Otherwise continue.
3. ...

## When things go wrong
| Problem | Fix | Escalate to |
|---|---|---|

## Checklist
- [ ] <short version of each step, for repeat users>

## Change log
| Date | Change | By |
|---|---|---|
```

## Rules

- Steps start with a verb. "Open", "Export", "Check".
- Name exact buttons, fields and values in **bold**.
- Roles, not names ("CS lead", not "Priya").
- One SOP per task. If the source covers two tasks, write two and link them.
