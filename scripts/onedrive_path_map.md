# OneDrive ↔ repo path map

Mirror the same nesting on OneDrive and in the GitHub repo so auto-catalog can infer project, topic, and category from the folder path.

## Canonical layout

```
Documents/Research Library/PDFs/Digestion/Indian Medical Knowledge/<Category>/file.pdf
```

Repo equivalent:

```
PDFs/Digestion/Indian Medical Knowledge/<Category>/file.pdf
```

`<Category>` must be one of:

- Primary texts & treatises
- Institutions & archives
- People & case studies
- Plants & remedies
- Colonial transfer & credit
- Method notes

## Folder name note

The live OneDrive root may still be named **Research Library Demo**. Treat that as the same root as **Research Library**:

```
Documents/Research Library Demo/PDFs/Digestion/Indian Medical Knowledge/<Category>/file.pdf
```

Either name is fine for the bot sync routine; keep the `PDFs/Digestion/...` subtree identical.

## Examples

| OneDrive | Repo |
|---|---|
| `…/PDFs/Digestion/Indian Medical Knowledge/Institutions & archives/wellcome-paira-mall-catalogue.pdf` | `PDFs/Digestion/Indian Medical Knowledge/Institutions & archives/wellcome-paira-mall-catalogue.pdf` |
| `…/PDFs/Digestion/Indian Medical Knowledge/Method notes/method-url-to-pdf-stamp.pdf` | `PDFs/Digestion/Indian Medical Knowledge/Method notes/method-url-to-pdf-stamp.pdf` |

## Sync flow

1. Drop PDF into the matching OneDrive category folder.  
2. Bot / scheduled sync copies new files into repo `PDFs/`.  
3. `scripts/auto_catalog.py` (Sync catalog Action) appends a `library.json` row from path + `tag-rules.json`.
