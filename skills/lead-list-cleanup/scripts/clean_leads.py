#!/usr/bin/env python3
"""Clean, validate and dedupe a lead list CSV.

Standard library only. Python 3.9+.

Usage:
    python clean_leads.py input.csv --out cleaned.csv --report report.json
        [--dedupe-key email|domain|email,company]
        [--drop-free-email] [--required email,company]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from urllib.parse import urlparse

# Header variants mapped to canonical column names (compared after normalizing).
HEADER_ALIASES = {
    "email": {"email", "e-mail", "emailaddress", "workemail", "businessemail", "mail"},
    "first_name": {"firstname", "first", "givenname", "fname"},
    "last_name": {"lastname", "last", "surname", "familyname", "lname"},
    "full_name": {"name", "fullname", "contactname", "contact"},
    "company": {"company", "companyname", "organization", "organisation", "account", "accountname"},
    "title": {"title", "jobtitle", "position", "role", "designation"},
    "website": {"website", "url", "companywebsite", "site", "companyurl"},
    "domain": {"domain", "companydomain", "emaildomain"},
    "linkedin": {"linkedin", "linkedinurl", "personlinkedinurl", "linkedinprofile"},
    "phone": {"phone", "phonenumber", "mobile", "directphone"},
    "country": {"country", "countryname"},
}

FREE_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.in", "ymail.com",
    "outlook.com", "hotmail.com", "live.com", "msn.com", "icloud.com", "me.com",
    "aol.com", "proton.me", "protonmail.com", "gmx.com", "zoho.com", "mail.com",
    "rediffmail.com", "yandex.com",
}

ROLE_PREFIXES = {
    "info", "sales", "support", "hello", "contact", "admin", "team", "office",
    "marketing", "hr", "careers", "jobs", "billing", "help", "enquiries", "noreply",
}

EMAIL_RE = re.compile(r"^[a-z0-9._%+'-]+@[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}$")


def norm_header(h: str) -> str:
    return re.sub(r"[^a-z0-9]", "", h.lower())


def map_headers(headers: list[str]) -> tuple[dict[str, str], dict[str, str]]:
    """Return (original -> canonical) for every column, and a log of renamed ones."""
    mapping: dict[str, str] = {}
    renamed: dict[str, str] = {}
    used: set[str] = set()
    for h in headers:
        key = norm_header(h)
        canonical = next(
            (c for c, aliases in HEADER_ALIASES.items() if key in aliases and c not in used),
            None,
        )
        if canonical:
            used.add(canonical)
            mapping[h] = canonical
            if h != canonical:
                renamed[h] = canonical
        else:
            mapping[h] = h.strip()
    return mapping, renamed


def fix_case(value: str) -> str:
    if value.isupper() and len(value) > 3:
        return value.title()
    return value


def domain_from(row: dict[str, str]) -> str:
    if row.get("domain"):
        return row["domain"].lower().removeprefix("www.")
    email = row.get("email", "")
    if "@" in email:
        return email.split("@", 1)[1]
    site = row.get("website", "").strip()
    if site:
        if "://" not in site:
            site = "http://" + site
        host = urlparse(site).netloc.lower()
        return host.removeprefix("www.")
    return ""


def filled_count(row: dict[str, str]) -> int:
    return sum(1 for v in row.values() if v not in ("", None))


def clean(rows, dedupe_keys, drop_free, required):
    stats = {"rows_in": 0, "invalid_email": 0, "free_email_removed": 0,
             "missing_required": 0, "duplicates": 0, "role_addresses": 0}
    best: dict[tuple, dict[str, str]] = {}
    order: list[tuple] = []
    no_key_rows: list[dict[str, str]] = []

    for raw in rows:
        stats["rows_in"] += 1
        row = {k: (v or "").strip() for k, v in raw.items()}
        for col in ("first_name", "last_name", "full_name", "company", "title"):
            if col in row:
                row[col] = fix_case(row[col])

        if row.get("full_name") and not (row.get("first_name") or row.get("last_name")):
            parts = row["full_name"].split()
            row["first_name"] = parts[0]
            row["last_name"] = " ".join(parts[1:])

        email = row.get("email", "").lower()
        row["email"] = email
        if email and not EMAIL_RE.match(email):
            stats["invalid_email"] += 1
            continue

        email_domain = email.split("@", 1)[1] if "@" in email else ""
        is_free = email_domain in FREE_EMAIL_DOMAINS
        # A personal inbox says nothing about the company, so prefer the website.
        if is_free and row.get("website") and not row.get("domain"):
            row["domain"] = domain_from({"website": row["website"]})
        else:
            row["domain"] = domain_from(row)
        row["free_email"] = "true" if is_free else "false"
        local = email.split("@", 1)[0] if email else ""
        is_role = local in ROLE_PREFIXES
        row["role_address"] = "true" if is_role else "false"

        if drop_free and is_free:
            stats["free_email_removed"] += 1
            continue
        if any(not row.get(col) for col in required):
            stats["missing_required"] += 1
            continue
        if is_role:
            stats["role_addresses"] += 1

        key = tuple(row.get(k, "").lower() for k in dedupe_keys)
        if not any(key):
            no_key_rows.append(row)
            continue
        if key in best:
            stats["duplicates"] += 1
            if filled_count(row) > filled_count(best[key]):
                best[key] = row
        else:
            best[key] = row
            order.append(key)

    out = [best[k] for k in order] + no_key_rows
    stats["rows_out"] = len(out)
    return out, stats


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("--out", default="cleaned.csv")
    p.add_argument("--report", default="report.json")
    p.add_argument("--dedupe-key", default="email")
    p.add_argument("--drop-free-email", action="store_true")
    p.add_argument("--required", default="")
    args = p.parse_args(argv)

    dedupe_keys = [k.strip() for k in args.dedupe_key.split(",") if k.strip()]
    required = [k.strip() for k in args.required.split(",") if k.strip()]

    try:
        with open(args.input, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                print("error: input has no header row", file=sys.stderr)
                return 2
            mapping, renamed = map_headers(reader.fieldnames)
            rows = ({mapping[k]: v for k, v in r.items() if k is not None} for r in reader)
            cleaned, stats = clean(rows, dedupe_keys, args.drop_free_email, required)
    except FileNotFoundError:
        print(f"error: file not found: {args.input}", file=sys.stderr)
        return 2
    except UnicodeDecodeError:
        print("error: file is not UTF-8. Re-save it as CSV UTF-8 and retry.", file=sys.stderr)
        return 2

    fields: list[str] = []
    for r in cleaned:
        for k in r:
            if k not in fields:
                fields.append(k)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(cleaned)

    stats["dedupe_key"] = dedupe_keys
    stats["mapped_columns"] = renamed
    with open(args.report, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
