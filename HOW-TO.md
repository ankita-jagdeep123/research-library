# HOW-TO — Research Library for Ankita

Plain-language process so you (and anyone covering for you) can keep the library tidy.

---

## 1. Hierarchy (keep this consistent)

```
Digestion                          ← main book / project
├── Indian Medical Knowledge       ← active topic
│   └── filter by TYPE (uniform):
│         Primary texts & treatises
│         Institutions & archives
│         People & case studies
│         Plants & remedies
│         Colonial transfer & credit
│         Method notes
├── Arts                           ← coming soon
└── Dance                          ← coming soon
```

**Do not** put book titles (e.g. Hortus) and people names (e.g. Paira Mall) as peer filter chips. Those belong in titles/tags; chips stay as *types*.

---

## 2. Recommended OneDrive layout

```
Research Library/
├── index.html
├── library.json
├── README.md
├── HOW-TO.md
└── PDFs/
    └── Digestion/
        └── Indian Medical Knowledge/
            ├── Primary texts & treatises/
            ├── Institutions & archives/
            ├── People & case studies/
            ├── Plants & remedies/
            ├── Colonial transfer & credit/
            └── Method notes/
```

- One catalog (`library.json`) at the root.  
- Binaries under `PDFs/.../{type}/`.  
- Filenames: kebab-case (`wellcome-paira-mall-catalogue.pdf`).

Repo `PDFs/` mirrors OneDrive nesting: Digestion → topic → type folder. Keep OneDrive the same shape so paths stay predictable.

---

## 3. Why this instead of Airtable

| Need | This kit | Airtable |
|---|---|---|
| Boss opens a PDF fast | ✅ Primary action on every card | Extra clicks / attachments |
| Works in OneDrive you already use | ✅ | Separate product |
| Hierarchy + type filters + search | ✅ | ✅ But files still live elsewhere |
| Zero build / zero vendor lock for files | ✅ | Catalog lock-in risk |

Migrate rows later to a Microsoft List if needed; **keep the PDFs**.

---

## 4. Checklist — add a source

### Preferred: GitHub Issue form (no hand-editing)

Live site: https://ankita-jagdeep123.github.io/research-library/

1. Open **Digestion → Indian Medical Knowledge** → **Add source** (or use the [issue form](https://github.com/ankita-jagdeep123/research-library/issues/new?template=add_source.yml)).  
2. Fill title, author, year, category (one of the six types), topic (default `indian-medical-knowledge`), tags/note, and URLs.  
3. For `pdfUrl`: public https PDF, relative `PDFs/…` for repo samples, or a OneDrive **Anyone with the link → Can view** link for private files. **Do not put secrets in the repo.** Private OneDrive PDFs stay as view links — they are not uploaded by the Action.  
4. Submit. The `ingest-source` Action appends to `library.json`, commits to `main`, comments on the issue, and closes it. Pages updates after the build.  
5. See `docs/ADD-SOURCE.md` for the short boss-facing how-to.

### Manual fallback (edit JSON)

1. Confirm it belongs under **Digestion → Indian Medical Knowledge** (or note a future topic).  
2. Pick **one uniform type** from the six filter types above.  
3. Get a durable PDF (public URL or stamped local PDF — next section).  
4. Optional: add a Wayback URL if the live page may vanish or paywall.  
5. Edit `library.json` — add under `sources`:
   - `id`, `title`, `author`, `year`
   - `topicId`: `"indian-medical-knowledge"`
   - `category`: exact string from `categories`
   - `tags`, `note`, `status`
   - `pdfUrl`, `originalUrl`, `waybackUrl`
6. Bump `meta.updated`.  
7. Open the live site (or local `index.html`) → Digestion → Indian Medical Knowledge → confirm card + **Open PDF**.  
8. If Pages is separate from OneDrive PDFs, use **Anyone with the link → Can view** links in `pdfUrl`.

### Adding a new Digestion topic later

Edit `hierarchy.topics` in `library.json`: set `status` to `"active"` and add sources with matching `topicId`. Coming-soon stubs (`arts`, `dance`) are already placeholders.

---

## 5. Turn a URL into a stamped PDF (page 1 provenance)

### Manual

1. Open the page → **Print → Save as PDF**.  
2. Optional one-page cover: Original URL · Archived date · Title.  
3. Save under the right type folder; point `pdfUrl` at it; set `originalUrl`.

### What “good” looks like

- Page 1 always shows provenance.  
- Page 2+ = short fair-use extract, not a pirate full-text dump.

### Later automation

Scripts (reportlab / weasyprint) can stamp page 1; keep human review for copyright.

---

## 6. Share with your boss

**Option A — live Pages (default):** Send https://ankita-jagdeep123.github.io/research-library/ — Digestion → Indian Medical Knowledge → filter / search → Open PDF. Use **Add source** to contribute rows.  

**Option B — OneDrive folder:** Share the synced folder; he opens `index.html` locally (embedded fallback works offline).  

**Option C:** Send a zip once for a meeting; prefer A/B ongoing.

Private PDFs: keep them on OneDrive and paste view links into `pdfUrl` via the issue form — never commit secrets.

---

## 7. Scaling without redoing PDFs

- Low hundreds of rows: stay on `library.json`.  
- Huge catalog: Microsoft List / Sheet / API for rows; same PDF folders.  
- New filter type: add to `categories` and use consistently.  
- New Digestion strand: activate a topic stub; don’t invent peer chips that mix people with book titles.

---

## 8. Copyright caution

Host only what you own, public domain, or clearly licensed. Prefer linking IA / BHL / publisher PDFs when stable and legal. Stamped catalogue summaries are research aids, not licensed full texts.

---

## 9. Short pitch

> Open https://ankita-jagdeep123.github.io/research-library/ → Digestion → Indian Medical Knowledge. Filter by source type (texts, archives, people, etc.) or search, then Open PDF. Add rows with **Add source** (GitHub Issue → Action updates the catalog). Arts and Dance topics are placeholders for later Digestion work.


---

## 10. Automatic tags

Drop a PDF into the right type folder under `PDFs/Digestion/<Topic>/<Category>/` (on GitHub or after sync from OneDrive). The **Sync catalog** Action (`scripts/auto_catalog.py`) walks `PDFs/`, infers category / topic / tags from the path and `tag-rules.json`, and appends a `library.json` row. You do **not** need to ask the bot for tags.

- Edit **`tag-rules.json`** on GitHub to teach new filename keywords or category hints — no code change required.
- Existing catalog rows are left alone (manual titles, notes, authors stay).
- Trigger: push to `PDFs/**` / `tag-rules.json`, weekday schedule, site **Sync now** button, **Actions → Sync catalog → Run workflow**, or open a **Sync now** issue (`[Sync] …` / label `sync-now`).

### AI tagging (optional)

When repo secret **`OPENAI_API_KEY`** is set, new sources also get AI-enriched title / author / year / category / tags / note (PDF text via `pdftotext` when available). Optional secrets: `OPENAI_BASE_URL` (default `https://api.openai.com/v1`), `OPENAI_MODEL` (default `gpt-4o-mini`). **Without the key**, folder + filename rules still work — AI is never required.

## 11. OneDrive → GitHub sync

Keep OneDrive folders mirroring the repo tree:

```
Documents/Research Library/PDFs/Digestion/Indian Medical Knowledge/<Category>/file.pdf
```

(Your live OneDrive folder may still be named **Research Library Demo** — same nesting under `PDFs/` either way. See `scripts/onedrive_path_map.md`.)

1. Drop new PDFs into the matching OneDrive category folder.  
2. A **Grok Bot / scheduled sync** copies new OneDrive PDFs into the repo `PDFs/` tree, then auto-catalog runs and updates `library.json`.  
3. Until Microsoft Graph secrets are added for a pure Actions-only OneDrive pull, the bot routine handles OneDrive → repo copies.  
4. You can also **upload PDFs directly on GitHub** into the nested `PDFs/…` folders; the Sync catalog Action will pick them up on push.

**OneDrive vs GitHub (summary)**

- **OneDrive** — working store for research PDFs (especially private).  
- **GitHub** — catalog UI (`index.html` + `library.json`) + public/sample PDFs under `PDFs/`.  
- Private files you must not publish: keep on OneDrive and paste *Anyone with the link → Can view* into `pdfUrl` via **Add source**.  
- Public / stampable samples: drop into mirrored folders → sync → auto-tags.


## 12. Topic descriptions (where they live)

Topic blurbs (e.g. Indian Medical Knowledge) live in **`library.json`** under `hierarchy.topics[].description` — **not** in `index.html`. The site loads `library.json` (with an embedded `LIBRARY_FALLBACK` copy for offline/OneDrive). Edit the JSON description field and refresh; clear it to hide the lede under the topic title.

## 13. Sync now (refresh catalog)

Three ways to refresh the catalog immediately for PDFs already in the repo:

1. **Site button** — Digestion → Indian Medical Knowledge → **Sync now** opens the Sync catalog workflow; click **Run workflow** on GitHub.
2. **Actions UI** — https://github.com/ankita-jagdeep123/research-library/actions/workflows/sync-catalog.yml → Run workflow.
3. **Issue form** — [Sync now](https://github.com/ankita-jagdeep123/research-library/issues/new?template=sync_now.yml) (`[Sync] Refresh catalog` / label `sync-now`) runs auto-catalog, comments, and closes.

OneDrive-only new files (not yet pushed to GitHub) still need the weekday ~7am bot sync, or message Ankita's Bot “sync now”.
