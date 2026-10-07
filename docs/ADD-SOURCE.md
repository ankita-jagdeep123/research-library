# Add a source (no hand-editing HTML)

For **Ankita** and anyone covering (including your boss who just needs the site).

## Live site

https://ankita-jagdeep123.github.io/research-library/

## Fast path (recommended)

1. On the site, open **Digestion → Indian Medical Knowledge**.
2. Click **Add source** (opens a GitHub Issue form).
3. Fill **Title**, **Author**, **Year**, **Category** (one of the six uniform types), **Topic** (default `indian-medical-knowledge`), optional tags/note/URLs, and **pdfUrl**.
4. Submit. A GitHub Action appends a row to `library.json`, commits to `main`, comments on the issue, and closes it.
5. Wait a minute for GitHub Pages to rebuild, then refresh the site and search for the new title.

Direct form (if the button is missing):  
https://github.com/ankita-jagdeep123/research-library/issues/new?template=add_source.yml

## What to put in `pdfUrl`

| Situation | Use |
|---|---|
| Public PDF or catalogue viewer | Full `https://…` URL |
| Demo sample already in the repo | Relative path like `PDFs/example.pdf` |
| Private OneDrive PDF | OneDrive **Anyone with the link → Can view** link — do **not** upload private files or secrets into this public repo |

## Enable auto-ingest (one-time)

If submitting the form does not update `library.json` automatically, the Action YAML is not on `main` yet (OAuth `workflow` scope). Follow [`ENABLE-INGEST-WORKFLOW.md`](ENABLE-INGEST-WORKFLOW.md). Until then, edit `library.json` manually or paste the form values by hand.

## Manual edit (fallback)

If the Action fails, edit `library.json` by hand (see root `HOW-TO.md`) and push to `main`. The embedded fallback inside `index.html` is only for offline/`file://`; the live Pages site always loads `library.json`.

## Copyright

Only link or host what you own, public domain, or clearly licensed. Prefer linking stable public PDFs (IA, BHL, publishers) when legal.
