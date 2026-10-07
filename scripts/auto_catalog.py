#!/usr/bin/env python3
"""Walk PDFs/ and append new local-pdf entries to library.json using tag-rules.json."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LIBRARY_PATH = REPO_ROOT / "library.json"
RULES_PATH = REPO_ROOT / "tag-rules.json"
PDFS_DIR = REPO_ROOT / "PDFs"

YEAR_RE = re.compile(r"\b((?:19|20)\d{2})\b")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
TOKEN_SPLIT_RE = re.compile(r"[-_\s]+")


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: dict) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def slugify(stem: str) -> str:
    s = stem.lower().strip()
    s = NON_ALNUM_RE.sub("-", s).strip("-")
    return s or "source"


def humanize_title(stem: str) -> str:
    parts = TOKEN_SPLIT_RE.split(stem.strip())
    words = []
    for p in parts:
        if not p:
            continue
        if p.isdigit() and len(p) == 4:
            words.append(p)
        elif p.isupper() and len(p) <= 4:
            words.append(p)
        else:
            words.append(p[:1].upper() + p[1:] if p else p)
    return " ".join(words) or stem


def unique_id(base: str, existing_ids: set[str]) -> str:
    if base not in existing_ids:
        return base
    n = 2
    while f"{base}-{n}" in existing_ids:
        n += 1
    return f"{base}-{n}"


def map_alias(raw: str, aliases: dict[str, str]) -> str | None:
    key = raw.strip().lower()
    if key in aliases:
        return aliases[key]
    # also try kebab form of the raw string
    kebab = NON_ALNUM_RE.sub("-", key).strip("-")
    if kebab in aliases:
        return aliases[kebab]
    return None


def category_from_path(parts: list[str], categories: list[str]) -> str | None:
    cat_set = set(categories)
    for part in parts:
        if part in cat_set:
            return part
    return None


def topic_from_path(parts: list[str], topic_aliases: dict[str, str]) -> str | None:
    # Prefer topic-like segments (not PDFs, not project, not category)
    for part in parts:
        mapped = map_alias(part, topic_aliases)
        if mapped:
            return mapped
    return None


def project_from_path(parts: list[str], project_aliases: dict[str, str]) -> str | None:
    for part in parts:
        mapped = map_alias(part, project_aliases)
        if mapped:
            return mapped
    return None


def category_from_filename(stem: str, category_keywords: dict[str, list[str]], default: str) -> str:
    lower = stem.lower()
    best: str | None = None
    best_hits = 0
    for cat, kws in category_keywords.items():
        hits = sum(1 for kw in kws if kw.lower() in lower)
        if hits > best_hits:
            best_hits = hits
            best = cat
    return best if best_hits > 0 and best else default


def tags_from_filename(stem: str, filename_keywords: dict[str, list[str]]) -> list[str]:
    lower = stem.lower()
    tags: list[str] = []
    seen: set[str] = set()
    for key, tag_list in filename_keywords.items():
        if key.lower() in lower:
            for t in tag_list:
                if t.lower() not in seen:
                    tags.append(t)
                    seen.add(t.lower())
    # cleaned tokens from stem
    for tok in TOKEN_SPLIT_RE.split(stem):
        if not tok:
            continue
        if YEAR_RE.fullmatch(tok):
            continue
        if len(tok) < 3:
            continue
        cleaned = tok.replace("_", "-")
        # Prefer title-ish token
        display = cleaned if cleaned.isupper() else cleaned[:1].upper() + cleaned[1:]
        if display.lower() not in seen:
            tags.append(display)
            seen.add(display.lower())
        if len(tags) >= 12:
            break
    return tags


def extract_year(stem: str) -> int | None:
    m = YEAR_RE.search(stem)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def discover_pdfs() -> list[Path]:
    if not PDFS_DIR.is_dir():
        return []
    files = []
    for p in PDFS_DIR.rglob("*"):
        if p.is_file() and p.suffix.lower() == ".pdf":
            files.append(p)
    return sorted(files)


def relative_pdf_url(path: Path) -> str:
    # Preserve spaces / special chars as in current library.json style
    return path.relative_to(REPO_ROOT).as_posix()


def catalog_one(
    path: Path,
    rules: dict,
    library: dict,
    existing_urls: set[str],
    existing_ids: set[str],
) -> dict | None:
    rel_url = relative_pdf_url(path)
    if rel_url in existing_urls:
        return None

    stem = path.stem
    # Relative parts under PDFs/
    try:
        under = path.relative_to(PDFS_DIR)
    except ValueError:
        under = path
    parts = list(under.parts[:-1])  # folders only

    categories = rules.get("categories") or library.get("categories") or []
    topic_aliases = rules.get("topic_aliases") or {}
    project_aliases = rules.get("project_aliases") or {}
    default_topic = rules.get("default_topic_id") or "indian-medical-knowledge"
    default_category = rules.get("default_category") or "Method notes"
    category_keywords = rules.get("category_keywords") or {}
    filename_keywords = rules.get("filename_keywords") or {}

    category = category_from_path(parts, categories)
    if not category:
        category = category_from_filename(stem, category_keywords, default_category)

    topic_id = topic_from_path(parts, topic_aliases) or default_topic
    # project mapped for future use / validation (stored only if hierarchy matches)
    _project = project_from_path(parts, project_aliases)

    base_id = slugify(stem)
    src_id = unique_id(base_id, existing_ids)
    year = extract_year(stem)
    tags = tags_from_filename(stem, filename_keywords)

    entry = {
        "id": src_id,
        "title": humanize_title(stem),
        "author": None,
        "year": year,
        "type": "local-pdf",
        "category": category,
        "tags": tags,
        "note": None,
        "status": "live",
        "pdfUrl": rel_url,
        "originalUrl": None,
        "waybackUrl": None,
        "topicId": topic_id,
    }
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-catalog PDFs/ into library.json")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    args = parser.parse_args()

    if not LIBRARY_PATH.is_file():
        print(f"error: missing {LIBRARY_PATH}", file=sys.stderr)
        return 1
    if not RULES_PATH.is_file():
        print(f"error: missing {RULES_PATH}", file=sys.stderr)
        return 1

    library = load_json(LIBRARY_PATH)
    rules = load_json(RULES_PATH)

    sources = library.get("sources")
    if not isinstance(sources, list):
        sources = []
        library["sources"] = sources

    existing_urls = {s.get("pdfUrl") for s in sources if isinstance(s, dict) and s.get("pdfUrl")}
    existing_ids = {s.get("id") for s in sources if isinstance(s, dict) and s.get("id")}

    pdfs = discover_pdfs()
    added = 0
    skipped = 0
    new_entries: list[dict] = []

    for pdf in pdfs:
        entry = catalog_one(pdf, rules, library, existing_urls, existing_ids)
        if entry is None:
            skipped += 1
            continue
        new_entries.append(entry)
        existing_urls.add(entry["pdfUrl"])
        existing_ids.add(entry["id"])
        added += 1

    if new_entries:
        sources.extend(new_entries)
        meta = library.setdefault("meta", {})
        meta["updated"] = date.today().isoformat()

    print(f"added {added}, skipped {skipped}")
    if args.dry_run:
        for e in new_entries:
            print(f"  + {e['id']}: {e['pdfUrl']} [{e['category']}] topic={e['topicId']}")
        print("dry-run: library.json not written")
        return 0

    if new_entries:
        write_json(LIBRARY_PATH, library)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
