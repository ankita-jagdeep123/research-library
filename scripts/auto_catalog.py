#!/usr/bin/env python3
"""Walk PDFs/ and append new local-pdf entries to library.json using tag-rules.json.

Optional AI enrichment (title/author/year/category/tags/note) when OPENAI_API_KEY
is set. Failures never abort the run — rule-based drafts are kept.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LIBRARY_PATH = REPO_ROOT / "library.json"
RULES_PATH = REPO_ROOT / "tag-rules.json"
PDFS_DIR = REPO_ROOT / "PDFs"

YEAR_RE = re.compile(r"\b((?:19|20)\d{2})\b")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
TOKEN_SPLIT_RE = re.compile(r"[-_\s]+")
JSON_OBJECT_RE = re.compile(r"\{[\s\S]*\}")

DEFAULT_OPENAI_BASE = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
PDF_TEXT_LIMIT = 2500
TAG_CAP = 10


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


JUNK_TAGS = {
    "pdf", "record", "page", "archive", "scan", "plates", "article", "faq", "catalogue",
    "history", "medicine", "india", "science", "research", "document", "local copy",
}


VOL_RE = re.compile(r"(?:^|[^a-z])(?:vol(?:ume)?)[\s._-]*0*(\d{1,3})(?![0-9])", re.I)


def apply_series(entry: dict, stem: str) -> None:
    """Multi-volume works: derive seriesId + sequence from 'vol N' in the filename.

    Runs after AI enrichment so AI can never change ordering. The series id is the
    filename text before 'vol', e.g. hortus-indicus-malabaricus-vol-03-... ->
    seriesId 'hortus-indicus-malabaricus', sequence 3. Must match existing rows'
    seriesId so new volumes sort next to old ones.
    """
    m = VOL_RE.search(stem)
    if not m:
        return
    prefix = stem[: m.start()].strip(" ._-")
    if not prefix:
        return
    sid = slugify(prefix)
    if sid == "hortus-indicus-malabaricus":
        sid = "hortus-malabaricus"  # existing series id in library.json
    entry["seriesId"] = sid
    entry["sequence"] = int(m.group(1))


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
    # Filename tokens are NOT used as tags any more (they produced junk such as
    # "Wipo", "Magazine"). Only curated filename_keywords from tag-rules.json apply.
    for tok in ([] if True else TOKEN_SPLIT_RE.split(stem)):
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
        # OneDrive is the home of every PDF. The sync routine fills onedriveShareUrl
        # (view-only anonymous link); the site's "Open PDF" prefers it over pdfUrl.
        "onedrivePath": "Documents/Research Library Demo/" + rel_url,
        "onedriveShareUrl": None,
        "originalUrl": None,
        "waybackUrl": None,
        "topicId": topic_id,
    }
    return entry


def extract_pdf_text(path: Path, limit: int = PDF_TEXT_LIMIT) -> str | None:
    """Extract text from the first two pages via pdftotext if available."""
    if not shutil.which("pdftotext"):
        return None
    try:
        proc = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "2", "-layout", str(path), "-"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    text = (proc.stdout or "").strip()
    if not text:
        return None
    if len(text) > limit:
        text = text[:limit]
    return text


def _openai_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip())


def _parse_year_ai(raw) -> int | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, int):
        return raw if 1000 <= raw <= 2100 else None
    if isinstance(raw, float):
        y = int(raw)
        return y if 1000 <= y <= 2100 else None
    s = str(raw).strip()
    m = YEAR_RE.search(s)
    if not m:
        return None
    try:
        y = int(m.group(1))
    except ValueError:
        return None
    return y if 1000 <= y <= 2100 else None


def merge_tags(rule_tags: list, ai_tags) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for source in (rule_tags or [], ai_tags or []):
        if not isinstance(source, list):
            continue
        for t in source:
            if not isinstance(t, str):
                continue
            cleaned = t.strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(cleaned)
            if len(out) >= TAG_CAP:
                return out
    return out


def call_openai_enrich(entry: dict, pdf_text: str | None, categories: list[str]) -> dict | None:
    """POST chat completions; return parsed STRICT JSON dict or None on failure."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return None
    base = (os.environ.get("OPENAI_BASE_URL") or DEFAULT_OPENAI_BASE).rstrip("/")
    model = (os.environ.get("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL).strip() or DEFAULT_OPENAI_MODEL

    cats = ", ".join(categories)
    excerpt = pdf_text or "(no PDF text extracted — use filename/path hints only)"
    system = (
        "You enrich research-library catalog metadata. "
        "Reply with STRICT JSON only — no markdown fences, no commentary. "
        'Schema: {"title": string, "author": string|null, "year": int|null, '
        '"category": string, "tags": string[], "note": string|null}. '
        f"category MUST be exactly one of: {cats}. "
        "tags: 3–6 meaningful subject keywords a historian would search for "
        "(people, places, plants, institutions, concepts, e.g. 'Paira Mall', 'chaulmoogra oil', "
        "'biopiracy', 'Ayurveda'). Proper capitalisation. NEVER use: words copied from the "
        "filename or URL, publisher/website names alone, document-format words "
        "(pdf, record, page, archive, scan, plates, article, faq, catalogue), years, "
        "single generic words (history, medicine, India, science, research), or duplicates."
    )
    user = (
        f"Rule-based draft:\n{json.dumps(entry, ensure_ascii=False)}\n\n"
        f"PDF text excerpt (pages 1–2, truncated):\n{excerpt}"
    )
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "response_format": {"type": "json_object"},
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        print(f"  AI API error for {entry.get('id')}: {exc}", file=sys.stderr)
        return None
    try:
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        print(f"  AI response shape error for {entry.get('id')}: {exc}", file=sys.stderr)
        return None
    if not isinstance(content, str):
        return None
    content = content.strip()
    # Strip accidental fences
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        m = JSON_OBJECT_RE.search(content)
        if not m:
            print(f"  AI JSON parse failed for {entry.get('id')}", file=sys.stderr)
            return None
        try:
            parsed = json.loads(m.group(0))
        except json.JSONDecodeError:
            print(f"  AI JSON parse failed for {entry.get('id')}", file=sys.stderr)
            return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def enrich_with_ai(entry: dict, pdf_path: Path, categories: list[str]) -> bool:
    """Mutate entry with AI fields when possible. Returns True if enriched."""
    if not _openai_available():
        return False
    try:
        pdf_text = extract_pdf_text(pdf_path)
        ai = call_openai_enrich(entry, pdf_text, categories)
        if not ai:
            return False

        title = ai.get("title")
        if isinstance(title, str) and title.strip():
            entry["title"] = title.strip()

        author = ai.get("author")
        if isinstance(author, str) and author.strip():
            entry["author"] = author.strip()
        elif author is None:
            pass  # keep rule-based (often None)

        year = _parse_year_ai(ai.get("year"))
        if year is not None:
            entry["year"] = year

        cat = ai.get("category")
        if isinstance(cat, str) and cat in categories:
            entry["category"] = cat
        # else keep folder/rule category

        note = ai.get("note")
        if isinstance(note, str) and note.strip():
            entry["note"] = note.strip()

        ai_tags = ai.get("tags") if isinstance(ai.get("tags"), list) else []
        ai_tags = [t for t in ai_tags if isinstance(t, str) and t.strip().lower() not in JUNK_TAGS]
        entry["tags"] = merge_tags(entry.get("tags") or [], ai_tags)
        return True
    except Exception as exc:  # noqa: BLE001 — never fail the whole run
        print(f"  AI enrich unexpected error for {entry.get('id')}: {exc}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto-catalog PDFs/ into library.json")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Force attempting AI enrichment (still no-op without OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Skip AI enrichment even if OPENAI_API_KEY is set",
    )
    args = parser.parse_args()

    if not LIBRARY_PATH.is_file():
        print(f"error: missing {LIBRARY_PATH}", file=sys.stderr)
        return 1
    if not RULES_PATH.is_file():
        print(f"error: missing {RULES_PATH}", file=sys.stderr)
        return 1

    library = load_json(LIBRARY_PATH)
    rules = load_json(RULES_PATH)
    categories = list(rules.get("categories") or library.get("categories") or [])

    # Default: attempt AI whenever key is present; --ai forces attempt; --no-ai disables
    want_ai = (not args.no_ai) and (_openai_available() or args.ai)
    if args.ai and not _openai_available():
        print("AI requested (--ai) but OPENAI_API_KEY not set — using rule-based only")
        want_ai = False
    elif want_ai and _openai_available():
        print(f"AI enrichment enabled (model={os.environ.get('OPENAI_MODEL') or DEFAULT_OPENAI_MODEL})")
    else:
        print("AI enrichment skipped (no OPENAI_API_KEY)")

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
    # Keep (entry, path) for AI after draft build
    pending: list[tuple[dict, Path]] = []

    for pdf in pdfs:
        entry = catalog_one(pdf, rules, library, existing_urls, existing_ids)
        if entry is None:
            skipped += 1
            continue
        pending.append((entry, pdf))
        apply_series(entry, pdf.stem)  # after AI: AI never touches ordering
        existing_urls.add(entry["pdfUrl"])
        existing_ids.add(entry["id"])
        added += 1

    for entry, pdf in pending:
        if want_ai and _openai_available():
            enriched = enrich_with_ai(entry, pdf, categories)
            if enriched:
                print(f"  AI enriched: {entry['id']}")
            else:
                print(f"  AI not applied (kept rules): {entry['id']}")
        else:
            print(f"  rules only: {entry['id']}")
        new_entries.append(entry)

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
