import { defineConfig } from 'astro/config';

// GitHub Pages typically serves under /<repo>/
const repo = process.env.GITHUB_REPOSITORY?.split('/')?.[1];
const base = repo ? `/${repo}` : '/';

export default defineConfig({
  site: process.env.SITE_URL || undefined,
  base,
  markdown: {
    shikiConfig: {
      theme: 'github-dark'
    }
  }
});
