#!/usr/bin/env python3
"""Clean, validate and dedupe a lead list CSV.

Standard library only. Python 3.9+. Reads only the input file, writes only the
two output files, makes no network calls.

Usage:
    python3 clean_leads.py input.csv [--out cleaned.csv] [--report report.json]
        [--dedupe-key email|domain|email,company]
        [--drop-free-email] [--required email,company]
        [--no-formula-escape]

By default outputs are written next to the input as
<input>.cleaned.csv and <input>.report.json.

Exit codes: 0 success, 2 input or usage error.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# Header variants mapped to canonical column names (compared after normalizing).
# Ambiguous headers such as a bare "Name" or "URL" are deliberately not mapped,
# because exports use them for both people and companies.
HEADER_ALIASES = {
    "email": {"email", "emailaddress", "workemail", "businessemail", "mail"},
    "first_name": {"firstname", "first", "givenname", "fname"},
    "last_name": {"lastname", "last", "surname", "familyname", "lname"},
    "full_name": {"fullname", "contactname", "personname"},
    "company": {"company", "companyname", "organization", "organisation", "account", "accountname"},
    "title": {"title", "jobtitle", "position", "role", "designation"},
    "website": {"website", "companywebsite", "site", "companyurl", "websiteurl"},
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
    "marketing", "hr", "careers", "jobs", "billing", "help", "enquiries",
    "noreply", "no-reply", "donotreply",
}

# Local part: no leading, trailing or doubled dots. Domain: labels of letters,
# digits and hyphens; the TLD may be punycode (xn--...).
EMAIL_RE = re.compile(
    r"^(?!\.)(?!.*\.\.)[a-z0-9._%+'-]+(?<!\.)@"
    r"(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+(?:[a-z]{2,}|xn--[a-z0-9-]+)$"
)

# Leading characters that make spreadsheet apps treat a cell as a formula.
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

NAME_COLUMNS = ("first_name", "last_name", "full_name")


class InputError(Exception):
    """A problem with the input that the user can fix."""


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


def fix_name_case(value: str) -> str:
    """Title-case person names written in all caps. Company names are left alone."""
    if value.isupper() and len(value) > 3:
        return value.title()
    return value


def host_of(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if "://" not in value:
        value = "http://" + value
    host = urlparse(value).netloc.lower().split("@")[-1].split(":")[0]
    return host.removeprefix("www.")


def escape_formula(value: str) -> str:
    if value and value.startswith(FORMULA_PREFIXES):
        return "'" + value
    return value


def filled_count(row: dict[str, str]) -> int:
    return sum(1 for v in row.values() if v not in ("", None))


def clean(rows, dedupe_keys, drop_free, required):
    stats = {
        "rows_in": 0, "invalid_email": 0, "free_email_removed": 0,
        "missing_required": 0, "duplicates": 0, "role_addresses": 0,
        "rows_without_dedupe_key": 0, "rows_with_extra_fields": 0,
    }
    best: dict[tuple, dict[str, str]] = {}
    order: list[tuple] = []
    no_key_rows: list[dict[str, str]] = []

    for raw in rows:
        stats["rows_in"] += 1
        extra = raw.pop(None, None)
        if extra:
            stats["rows_with_extra_fields"] += 1
        row = {k: (v or "").strip() for k, v in raw.items()}

        email = row.get("email", "").lower()
        if "email" in row:
            row["email"] = email
        if email and not EMAIL_RE.match(email):
            stats["invalid_email"] += 1
            continue

        local, _, email_domain = email.partition("@")
        is_role = local in ROLE_PREFIXES
        is_free = email_domain in FREE_EMAIL_DOMAINS

        for col in NAME_COLUMNS:
            if col in row:
                row[col] = fix_name_case(row[col])
        # Split a full name only for real people, not for "Sales Team" style rows.
        if (row.get("full_name") and not is_role
                and not (row.get("first_name") or row.get("last_name"))):
            parts = row["full_name"].split()
            row["first_name"] = parts[0]
            row["last_name"] = " ".join(parts[1:])

        # Company domain: an explicit domain column wins, then the email (unless it
        # is a personal inbox, which says nothing about the company), then website.
        if row.get("domain"):
            row["domain"] = host_of(row["domain"])
        elif email_domain and not is_free:
            row["domain"] = email_domain
        else:
            row["domain"] = host_of(row.get("website", ""))

        row["free_email"] = "true" if is_free else "false"
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
        if not all(key):
            stats["rows_without_dedupe_key"] += 1
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


def read_rows(path: Path):
    """Return (reader, file handle). Detects comma, semicolon or tab delimiters."""
    f = open(path, newline="", encoding="utf-8-sig")
    sample = f.read(64 * 1024)
    f.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    return csv.DictReader(f, dialect=dialect), f


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("input")
    p.add_argument("--out", help="cleaned CSV path (default: <input>.cleaned.csv)")
    p.add_argument("--report", help="JSON report path (default: <input>.report.json)")
    p.add_argument("--dedupe-key", default="email")
    p.add_argument("--drop-free-email", action="store_true")
    p.add_argument("--required", default="")
    p.add_argument("--no-formula-escape", action="store_true",
                   help="do not prefix cells starting with = + - @ with an apostrophe")
    args = p.parse_args(argv)

    csv.field_size_limit(min(sys.maxsize, 2**31 - 1))
    src = Path(args.input)
    out = Path(args.out) if args.out else src.with_name(src.stem + ".cleaned.csv")
    report = Path(args.report) if args.report else src.with_name(src.stem + ".report.json")
    dedupe_keys = [k.strip() for k in args.dedupe_key.split(",") if k.strip()]
    required = [k.strip() for k in args.required.split(",") if k.strip()]

    try:
        if not src.is_file():
            raise InputError(f"file not found: {src}")
        resolved = {src.resolve(), out.resolve(), report.resolve()}
        if len(resolved) < 3:
            raise InputError("--out, --report and the input file must all be different paths")
        if not dedupe_keys:
            raise InputError("--dedupe-key cannot be empty")

        reader, handle = read_rows(src)
        with handle:
            if not reader.fieldnames:
                raise InputError("input has no header row")
            mapping, renamed = map_headers(reader.fieldnames)
            available = set(mapping.values()) | {"domain"}  # domain is always derived
            missing = [k for k in dedupe_keys + required if k not in available]
            if missing:
                raise InputError(
                    f"column(s) not found: {', '.join(missing)}. "
                    f"Available after mapping: {', '.join(sorted(available))}"
                )
            rows = ({(mapping.get(k) if k is not None else None): v for k, v in r.items()} for r in reader)
            cleaned, stats = clean(rows, dedupe_keys, args.drop_free_email, required)
    except InputError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except UnicodeDecodeError:
        print("error: file is not UTF-8. Re-save it as 'CSV UTF-8' and retry.", file=sys.stderr)
        return 2
    except csv.Error as e:
        print(f"error: could not parse CSV ({e})", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"error: could not read input ({e})", file=sys.stderr)
        return 2

    fields: list[str] = [mapping[h] for h in reader.fieldnames]
    for r in cleaned:
        for k in r:
            if k not in fields:
                fields.append(k)
    if not args.no_formula_escape:
        cleaned = [{k: escape_formula(v) for k, v in r.items()} for r in cleaned]

    stats["dedupe_key"] = dedupe_keys
    stats["mapped_columns"] = renamed
    stats["formula_escape"] = not args.no_formula_escape
    stats["output"] = str(out)
    try:
        with open(out, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(cleaned)
        with open(report, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2)
    except OSError as e:
        print(f"error: could not write output ({e})", file=sys.stderr)
        return 2

    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
