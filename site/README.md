# Skills Catalog Site

This folder contains the source code for the skills catalog website.

## Data generation

The site content is derived from `**/SKILL.md` in this repository.

Run the generator from the repo root:

```bash
python3 .scripts/generate_site_data.py
```

It writes:

- `site/src/data/skills.json`
- `site/src/content/skills/*.md`

These files are generated and are not meant to be edited by hand.

## Local development

From the repo root:

```bash
python3 .scripts/generate_site_data.py
cd site
npm install
npm run dev
```

## Build

From the repo root:

```bash
python3 .scripts/generate_site_data.py
cd site
npm install
npm run build
```

## Deployment variables

- `SITE_URL`: absolute site origin used for canonical/absolute URLs. Defaults to `https://skills.jinzhezeng.group`.
- `SITE_BASE`: optional base path for subpath deployments such as GitHub Pages.
