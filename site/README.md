# Skills Site

This directory contains a small static site that is **auto-generated from this repository**.

- Source of truth: `**/SKILL.md`
- Generator: `scripts/generate_site_data.py`
- Output artifacts (generated at build time):
  - `site/src/data/skills.json`
  - `site/src/content/skills/*.md`

## Local preview

```bash
python3 scripts/generate_site_data.py
cd site
npm install
npm run dev
```

## CI

- PR build: `.github/workflows/site.yml`
- (Optional) GitHub Pages deploy: `.github/workflows/pages.yml`
