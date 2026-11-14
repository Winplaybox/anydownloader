// Writes sitemap.xml + public/sitemap.xml from the route table. Canonical-duplicate routes are excluded.
import fs from 'fs';
import { TOOL_ROUTES } from '../src/data/toolRoutes.js';
const SITE = 'https://ovd.winplaybox.in';
const today = new Date().toISOString().slice(0, 10);
const urls = [
  ['/', 1.0, 'daily'],
  ...TOOL_ROUTES.filter((r) => !r.canonical).map((r) => [r.path, 0.9, 'weekly']),
  ['/youtube-subscribe-link-generator', 0.9, 'weekly'],
  ['/ai-video-editor', 0.8, 'weekly'],
  ['/extension', 0.6, 'monthly'],
  ['/blog', 0.7, 'weekly'],
  ['/updates', 0.4, 'weekly'],
  ['/contact', 0.3, 'yearly'],
  ['/privacy', 0.2, 'yearly'],
  ['/terms', 0.2, 'yearly'],
  ['/dmca', 0.2, 'yearly'],
];
const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
  urls.map(([p, pr, cf]) => `  <url>\n    <loc>${SITE}${p}</loc>\n    <lastmod>${today}</lastmod>\n    <changefreq>${cf}</changefreq>\n    <priority>${pr}</priority>\n  </url>`).join('\n') + '\n</urlset>\n';
fs.writeFileSync('sitemap.xml', xml);
fs.mkdirSync('public', { recursive: true });
fs.writeFileSync('public/sitemap.xml', xml);
console.log(`sitemap: ${urls.length} urls`);
