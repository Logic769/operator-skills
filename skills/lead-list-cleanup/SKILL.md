---
name: lead-list-cleanup
description: Clean a prospect or lead list (CSV) before importing it into a CRM or outreach tool. Use when the user asks to clean, dedupe, normalize, validate or prepare a lead list, contact export or prospect spreadsheet.
---

# Lead list cleanup

Bad lists burn domains and pollute CRMs. This skill makes every list pass the same checks before it is used.

## Steps

1. **Run the script first.** Never dedupe or validate by reading rows yourself.

   ```bash
   python3 ${CLAUDE_SKILL_DIR}/scripts/clean_leads.py input.csv
   ```

   `${CLAUDE_SKILL_DIR}` is this skill's folder (Claude Code fills it in). Where it is not set, use the path to `scripts/clean_leads.py` next to this SKILL.md. Outputs go next to the input as `input.cleaned.csv` and `input.report.json`; set `--out` and `--report` to change that.

   Options:
   - `--dedupe-key email` (default), `domain`, or `email,company`
   - `--drop-free-email` removes gmail.com, yahoo.com, outlook.com and similar addresses (use for B2B lists)
   - `--required email,company` drops rows missing these columns
   - `--no-formula-escape` turns off spreadsheet formula protection (see below)

   Exit code 2 means an input problem (missing column, unreadable file); the message says what to fix.

2. **Read the report JSON** and summarize it for the user: rows in, rows out, duplicates removed, invalid emails, free email addresses, missing required fields, and which column names were mapped.

3. **Flag judgment calls** the script cannot make, by looking at a sample of 20 cleaned rows:
   - Role addresses (info@, sales@, support@). They are kept but marked `role_address=true`. Ask whether to keep them.
   - Companies that look like duplicates under different names ("Acme Inc" and "Acme").
   - Titles that do not match the user's target persona, if they gave one.

4. **Deliver** the cleaned CSV and a short summary. Do not import anywhere unless asked.

## What the script does

- Detects comma, semicolon or tab separated files.
- Maps common header variants (`E-mail`, `Email Address`, `work_email` become `email`; `Company Name`, `Organization` become `company`; and so on). Ambiguous headers like a bare `Name` or `URL` are left as they are.
- Trims whitespace, lowercases emails, title-cases person names written in all caps. Company names keep their case.
- Splits `full_name` into `first_name` and `last_name` when those are missing (not for role addresses).
- Derives the company `domain` from a domain column, a work email, or the website. Personal inboxes (gmail and similar) never count as a company domain.
- Validates email syntax (not deliverability).
- Adds `free_email` and `role_address` flag columns.
- Dedupes on the chosen key, keeping the row with the most filled fields. Rows missing the key are kept and counted, never merged.
- Escapes cells that start with `=`, `+`, `-` or `@` by adding a leading apostrophe, so a malicious value cannot run as a formula when the file is opened in Excel or Google Sheets. Phone numbers like `+1...` get the apostrophe too; pass `--no-formula-escape` if the file goes only into a CRM import.

## Output format

```
Cleaned 1,240 rows to 1,032.
- 148 duplicates removed (key: email)
- 37 invalid emails removed
- 23 rows missing required fields removed
- 61 role addresses kept and flagged
Mapped columns: "Email Address" to email, "Company Name" to company
Needs your call: keep role addresses? 3 possible duplicate companies listed below.
```

## Limits

Syntax checks do not prove an address can receive mail. For high-volume sends, run the cleaned file through a verification service.
