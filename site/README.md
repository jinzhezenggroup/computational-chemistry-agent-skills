# Skills Site

This directory contains a small static site that is **auto-generated from this repository**.

- Source of truth: `**/SKILL.md`
- Generator: `scripts/generate_site_data.py`
- Build system: [Astro](https://astro.build/) (static output)
- License: **LGPL-3.0-or-later** (repo root `LICENSE`)

## What gets generated

`python3 scripts/generate_site_data.py` scans `**/SKILL.md` and generates:

- `site/src/data/skills.json` (for listing/search)
- `site/src/content/skills/*.md` (Astro content collection pages)

These generated files are intentionally ignored by git (see `.gitignore`).

## Local preview

```bash
# from repo root
python3 scripts/generate_site_data.py

cd site
npm install
npm run dev
```

## Build

```bash
# from repo root
python3 scripts/generate_site_data.py

cd site
npm install
npm run build
```

## Deployment

This repo does **not** ship GitHub Actions workflows for building/deploying the site.

Recommended options:
- GitHub Pages via your own workflow (outside this repo), or
- any static hosting (Vercel/Netlify/Nginx) by uploading `site/dist/` after `npm run build`.
