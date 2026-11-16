/**
 * Static prerender for SEO.
 *
 * Renders every URL in sitemap.xml with a headless browser and writes the final HTML
 * (real <title>, meta description, canonical, JSON-LD, H1 and body text) to
 * ./<route>/index.html in the deploy root. Hostinger's .htaccess serves an existing
 * directory before the SPA fallback, so search engines get full HTML without running JS.
 * The React app still boots on top of it for users.
 *
 *   npm run build:seo        (build + prerender)
 *   node scripts/prerender.mjs
 *
 * Needs Playwright once:  npm i -D playwright && npx playwright install chromium
 */
import fs from 'fs';
import http from 'http';
import path from 'path';

const root = path.resolve('.');
const SITE = 'https://ovd.winplaybox.in';
const PORT = Number(process.env.PRERENDER_PORT || 4599);

let chromium;
try {
  ({ chromium } = await import('playwright'));
} catch {
  console.warn('[prerender] Playwright not installed - skipping. Run: npm i -D playwright && npx playwright install chromium');
  process.exit(0);
}

const sitemap = fs.readFileSync(path.join(root, 'sitemap.xml'), 'utf-8');
const routes = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)]
  .map((m) => m[1].replace(SITE, '') || '/')
  .filter((r) => r !== '/' && !r.includes('.'));

const MIME = { '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.png': 'image/png', '.ico': 'image/x-icon', '.json': 'application/json', '.html': 'text/html' };
const shell = fs.readFileSync(path.join(root, 'index.html'), 'utf-8');

const server = http.createServer((req, res) => {
  const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const file = path.join(root, p);
  if (p !== '/' && file.startsWith(root) && fs.existsSync(file) && fs.statSync(file).isFile()) {
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
    return fs.createReadStream(file).pipe(res);
  }
  res.writeHead(200, { 'Content-Type': 'text/html' });
  res.end(shell); // always the SPA shell, never a previously prerendered page
});
await new Promise((r) => server.listen(PORT, r));

const browser = await chromium.launch();
const page = await browser.newPage();
// Never hit the real backend while prerendering
await page.route(/onrender\.com|googletagmanager|google-analytics|googlesyndication|pagead2/, (r) => r.abort());

let ok = 0;
for (const route of routes) {
  try {
    await page.goto(`http://localhost:${PORT}${route}`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForSelector('h1', { timeout: 8000 }).catch(() => {});
    let html = await page.content();
    html = html.replaceAll(`http://localhost:${PORT}`, SITE);
    // canonical must be the page itself (SPA shell carries the homepage canonical)
    html = html.replace(/<link rel="canonical" href="[^"]*"\s*\/?>/, `<link rel="canonical" href="${SITE}${route}">`);
    const outDir = path.join(root, route.replace(/^\/+/, ''));
    fs.mkdirSync(outDir, { recursive: true });
    fs.writeFileSync(path.join(outDir, 'index.html'), html, 'utf-8');
    ok++;
    console.log(`[prerender] ${route}`);
  } catch (e) {
    console.warn(`[prerender] FAILED ${route}: ${e.message}`);
  }
}

await browser.close();
server.close();
console.log(`[prerender] done: ${ok}/${routes.length} pages`);
