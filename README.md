# Infinity Foundation — Digestion Research Library

A lightweight, static research library for **Ankita Jagdeep** (Infinity Foundation): browse **Digestion → topic → uniform source types**, search, and open PDFs — without Airtable or a build step.

## Live site (GitHub Pages)

**https://ankita-jagdeep123.github.io/digestion-research-library/**

Repo: https://github.com/ankita-jagdeep123/digestion-research-library

## Browse hierarchy

1. **Digestion** — main book / research project  
2. **Topics under Digestion**
   - **Indian Medical Knowledge** (active demo)
   - **Arts**, **Dance** (coming-soon placeholders)
3. **Inside Indian Medical Knowledge** — filter chips are *uniform types* (not mixed book titles vs. people):
   - Primary texts & treatises  
   - Institutions & archives  
   - People & case studies  
   - Plants & remedies  
   - Colonial transfer & credit  
   - Method notes  

## What’s in this repo

| File / folder | Role |
|---|---|
| `index.html` | Static UI (hierarchy + search + type chips + cards). Works offline / `file://` via embedded fallback. |
| `library.json` | Catalog: hierarchy, filter types, sources. Live Pages always loads this file. |
| `PDFs/` | Local stamped archive PDFs for demo / sample Open PDF. |
| `HOW-TO.md` | How to stamp a URL, OneDrive layout, share with your boss. |
| `docs/ADD-SOURCE.md` | Add a source via GitHub Issue form (no hand-editing HTML). |
| `.github/ISSUE_TEMPLATE/add_source.yml` | Issue form fields for new sources. |
| `.github/workflows/ingest-source.yml` | Action that appends to `library.json` and commits. |

## Add a source (no HTML editing)

1. Open the live site → **Digestion → Indian Medical Knowledge** → **Add source**.  
2. Fill the GitHub Issue form (title, author, year, category, pdfUrl, …).  
3. Submit. The Action appends to `library.json`, pushes `main`, comments, and closes the issue. Pages rebuilds automatically.

Details: [`docs/ADD-SOURCE.md`](docs/ADD-SOURCE.md).

> **One-time setup:** the ingest Action YAML could not be pushed with the initial OAuth token (missing `workflow` scope). Enable it by copying `docs/ingest-source.workflow.yml` → `.github/workflows/ingest-source.yml` after `gh auth refresh -s workflow` — see [`docs/ENABLE-INGEST-WORKFLOW.md`](docs/ENABLE-INGEST-WORKFLOW.md). Until then, the Issue form and `library.json` still work; you can edit `library.json` manually or use the form and merge by hand.

**pdfUrl tip:** Private OneDrive PDFs stay as **Anyone with the link → Can view** links. Do not commit secrets or private binary dumps you are not allowed to publish. Sample PDFs under `PDFs/` remain in the repo so demo **Open PDF** works.

## Why OneDrive folders + this UI (not Airtable)

- **PDFs already live as files.** Your boss wants to *open* a PDF, not manage a database.
- **No seat licenses / no rebuild.** Plain files you already sync and share.
- **Hierarchy + type filters + search** beat Ctrl+F once the pile grows.
- Start here; migrate the *catalog* later if rows explode (PDFs stay put).

## Demo contents

- **12 sample sources** remapped under Indian Medical Knowledge into the six uniform types (Plants & remedies is ready as a chip; no demo row mapped there yet).
- **Real public PDFs** where possible (Current Science, Internet Archive, BHL hub).
- **Local stamped PDFs** under `PDFs/`.

## Quick start for your boss

1. Open https://ankita-jagdeep123.github.io/digestion-research-library/  
2. Open **Digestion** → **Indian Medical Knowledge**.  
3. Filter by type or search → **Open PDF**.  
4. To contribute a row: **Add source**.

## Copyright caution

Only host PDFs you own rights to, that are public domain, or clearly licensed for this use. Do **not** mass-upload copyrighted books.

## Scaling path

When `library.json` gets huge: keep the same UI; later point it at a Microsoft List or small API. **You do not redo the PDFs.** See `HOW-TO.md`.
