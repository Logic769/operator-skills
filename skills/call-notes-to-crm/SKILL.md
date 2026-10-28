---
name: call-notes-to-crm
description: Convert raw sales or customer call notes or a transcript into structured CRM updates, next steps with owners and dates, and a follow-up email. Use when the user shares call notes, a meeting transcript or a recording summary and wants the CRM updated, a recap written or next steps pulled out.
---

# Call notes to CRM

The value of a call disappears if the CRM is not updated the same day. This skill turns notes into the exact fields a rep would fill in.

## Steps

1. **Read the full notes or transcript.** Identify the account, people on the call and their roles.
2. **Extract only what was said.** Every field must trace to the source. If it is not in the notes, leave the field blank and list it under "Not covered".
3. **Fill the template below.**
4. **If a CRM connector is available** (HubSpot, Salesforce, Attio, Pipedrive), show the proposed changes as a diff and wait for a yes before writing.

## Template

```
Account: <company>         Deal/opportunity: <name if known>
Call date: <date>          Attendees: <name (role, side)>

Stage change: <from> to <to>, or "no change"
Pain (their words): "<short quote>"
Current solution: ...
Decision process: <who decides, who signs, steps>
Budget: <stated amount or range, or blank>
Timeline: <stated date or event>
Competitors mentioned: ...
Objections: ...
Risk level: Low / Medium / High, with one-line reason

Next steps
| Action | Owner | Due |
|---|---|---|

Not covered (ask next time): ...
```

Then a follow-up email: under 120 words, recaps the agreed next steps and dates, no new pitch.

## Rules

- Quote pain in the customer's words. Do not paraphrase into marketing language.
- Never infer budget or authority. If unclear, it goes under "Not covered".
- Dates are absolute (2026-11-04), not relative ("next Tuesday").
