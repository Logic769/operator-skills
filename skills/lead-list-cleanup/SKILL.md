---
name: lead-list-cleanup
description: Clean a prospect or lead list (CSV) before importing it into a CRM or outreach tool. Use when the user asks to clean, dedupe, normalize, validate or prepare a lead list, contact export or prospect spreadsheet.
---

# Lead list cleanup

Bad lists burn domains and pollute CRMs. This skill makes every list pass the same checks before it is used.

## Steps

1. **Run the script first.** Never dedupe or validate by reading rows yourself.

   ```bash
   python scripts/clean_leads.py input.csv --out cleaned.csv --report report.json
   ```

   Options:
   - `--dedupe-key email` (default), `domain`, or `email,company`
   - `--drop-free-email` removes gmail.com, yahoo.com, outlook.com and similar addresses (use for B2B lists)
   - `--required email,company` drops rows missing these columns

2. **Read `report.json`** and summarize it for the user: rows in, rows out, duplicates removed, invalid emails, free email addresses, missing required fields, and which column names were mapped.

3. **Flag judgment calls** the script cannot make, by looking at a sample of 20 cleaned rows:
   - Role addresses (info@, sales@, support@). They are kept but marked `role_address=true`. Ask whether to keep them.
   - Companies that look like duplicates under different names ("Acme Inc" and "Acme").
   - Titles that do not match the user's target persona, if they gave one.

4. **Deliver** `cleaned.csv` and a short summary. Do not import anywhere unless asked.

## What the script does

- Maps common header variants (`E-mail`, `Email Address`, `work_email` become `email`; `Company Name`, `Organization` become `company`; and so on).
- Trims whitespace, lowercases emails and domains, title-cases names written in all caps.
- Splits `full_name` into `first_name` and `last_name` when those are missing.
- Derives `domain` from the email or the website column.
- Validates email syntax (not deliverability).
- Adds `free_email` and `role_address` flag columns.
- Dedupes on the chosen key, keeping the row with the most filled fields.

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
