#!/usr/bin/env python3
"""Parse an Add-source GitHub issue body and append a row to library.json."""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

LIBRARY = Path("library.json")
FIELD_ALIASES = {
    "title": "title",
    "author": "author",
    "year": "year",
    "category": "category",
    "topic": "topic",
    "tags": "tags",
    "note": "note",
    "pdf / view url (pdfurl)": "pdfUrl",
    "pdfurl": "pdfUrl",
    "pdf / view url": "pdfUrl",
    "original url": "originalUrl",
    "wayback url": "waybackUrl",
    "status": "status",
}


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:80] or "source"


def parse_issue_body(body: str) -> dict:
    """Parse GitHub issue-form markdown (### Field\\n\\nvalue)."""
    fields: dict[str, str] = {}
    # Split on ### headings produced by issue forms
    parts = re.split(r"^###\s+", body or "", flags=re.MULTILINE)
    for part in parts[1:]:
        lines = part.splitlines()
        if not lines:
            continue
        label = lines[0].strip().lower()
        value_lines = lines[1:]
        # Drop leading blanks
        while value_lines and not value_lines[0].strip():
            value_lines.pop(0)
        # Stop at next blank-only trailing noise; join remaining non-_No response_
        raw = "\n".join(value_lines).strip()
        if raw in ("_No response_", "None", ""):
            raw = ""
        key = FIELD_ALIASES.get(label)
        if key:
            fields[key] = raw
    return fields


def null_if_empty(v: str | None):
    if v is None:
        return None
    v = v.strip()
    return v if v else None


def infer_type(pdf_url: str | None, status: str | None) -> str:
    u = (pdf_url or "").lower()
    st = (status or "").lower()
    if u.startswith("pdfs/") or "local" in st:
        return "local-pdf"
    if u.endswith(".pdf") or "pdf" in st:
        return "pdf"
    return "web"


def unique_id(base: str, existing: set[str]) -> str:
    if base not in existing:
        return base
    i = 2
    while f"{base}-{i}" in existing:
        i += 1
    return f"{base}-{i}"


def main() -> int:
    body = os.environ.get("ISSUE_BODY", "")
    issue_number = os.environ.get("ISSUE_NUMBER", "")
    fields = parse_issue_body(body)

    title = (fields.get("title") or "").strip()
    if not title:
        print("ERROR: Title is required", file=sys.stderr)
        return 1

    author = (fields.get("author") or "").strip() or "Unknown"
    year_raw = (fields.get("year") or "0").strip()
    try:
        year = int(re.sub(r"[^\d-]", "", year_raw) or "0")
    except ValueError:
        year = 0

    category = (fields.get("category") or "").strip()
    topic = (fields.get("topic") or "indian-medical-knowledge").strip()
    tags_raw = fields.get("tags") or ""
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    note = (fields.get("note") or "").strip()
    pdf_url = null_if_empty(fields.get("pdfUrl"))
    original_url = null_if_empty(fields.get("originalUrl"))
    wayback_url = null_if_empty(fields.get("waybackUrl"))
    status = (fields.get("status") or "Public PDF").strip()

    if not pdf_url:
        print("ERROR: pdfUrl is required", file=sys.stderr)
        return 1

    data = json.loads(LIBRARY.read_text(encoding="utf-8"))
    categories = data.get("categories") or []
    if category not in categories:
        print(f"ERROR: category must be one of {categories}", file=sys.stderr)
        return 1

    existing_ids = {s.get("id") for s in data.get("sources", []) if s.get("id")}
    new_id = unique_id(slugify(title), existing_ids)

    entry = {
        "id": new_id,
        "title": title,
        "author": author,
        "year": year,
        "type": infer_type(pdf_url, status),
        "category": category,
        "tags": tags,
        "note": note,
        "status": status,
        "pdfUrl": pdf_url,
        "originalUrl": original_url,
        "waybackUrl": wayback_url,
        "topicId": topic,
    }

    data.setdefault("sources", []).append(entry)
    if "meta" in data:
        data["meta"]["updated"] = date.today().isoformat()

    LIBRARY.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Outputs for the workflow
    out = Path(os.environ.get("GITHUB_OUTPUT", "/dev/stdout"))
    with out.open("a", encoding="utf-8") as fh:
        fh.write(f"id={new_id}\n")
        fh.write(f"title={title}\n")
        fh.write(f"issue={issue_number}\n")

    print(json.dumps(entry, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
