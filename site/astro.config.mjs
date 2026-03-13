import { defineConfig } from 'astro/config';

// Default to root for local dev and non-Pages deployments.
// For GitHub Pages, set SITE_BASE in repo/environment vars (e.g. "/<repo>").
const base = process.env.SITE_BASE || '/';

export default defineConfig({
  site: process.env.SITE_URL || undefined,
  base,
  markdown: {
    shikiConfig: {
      theme: 'github-light'
    }
  }
});
