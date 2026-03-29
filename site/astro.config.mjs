import { defineConfig } from 'astro/config';

const DEFAULT_SITE_URL = 'https://skills.jinzhezeng.group';

// Default to root for local dev and non-Pages deployments.
// For GitHub Pages, set SITE_BASE in repo/environment vars (e.g. "/<repo>").
const base = process.env.SITE_BASE || '/';
const site = process.env.SITE_URL || DEFAULT_SITE_URL;

export default defineConfig({
  site,
  base,
  markdown: {
    shikiConfig: {
      theme: 'github-light'
    }
  }
});
