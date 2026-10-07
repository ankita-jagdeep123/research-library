# Enable the Add-source ingest Action

The OAuth token used for the initial push did not include the `workflow` scope, so GitHub blocked committing `.github/workflows/ingest-source.yml`.

## One-time fix (Ankita)

From a machine where `gh` can open a browser (or complete device login):

```bash
cd /path/to/digestion-research-library   # or: git clone https://github.com/ankita-jagdeep123/digestion-research-library
gh auth refresh -h github.com -s repo,workflow,read:org,gist
mkdir -p .github/workflows
cp docs/ingest-source.workflow.yml .github/workflows/ingest-source.yml
git add .github/workflows/ingest-source.yml
git commit -m "Add ingest-source workflow"
git push origin main
```

Or in the GitHub UI: **Add file → Create new file** at path `.github/workflows/ingest-source.yml` and paste the contents of [`docs/ingest-source.workflow.yml`](ingest-source.workflow.yml).

After that, opening an issue with the **Add source** form (label `add-source`) will append to `library.json` and update Pages.
