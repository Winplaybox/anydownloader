import fs from 'fs';
import path from 'path';

const root = path.resolve('.');
const dist = path.join(root, 'dist');
const assetsDst = path.join(root, 'assets');

fs.mkdirSync(assetsDst, { recursive: true });

// 1. Copy all assets from dist/assets to ./assets
const distAssets = path.join(dist, 'assets');
let mainJsFile = null;
let mainCssFile = null;

if (fs.existsSync(distAssets)) {
  for (const file of fs.readdirSync(distAssets)) {
    const srcFile = path.join(distAssets, file);
    const dstFile = path.join(assetsDst, file);
    fs.copyFileSync(srcFile, dstFile);
    console.log(`Copied asset: assets/${file}`);

    if (file.startsWith('app-') && file.endsWith('.js')) {
      mainJsFile = file;
    }
    if (file.startsWith('style-') && file.endsWith('.css')) {
      mainCssFile = file;
    }
  }

  // Also maintain index.js and index.css as fallbacks
  if (mainJsFile) {
    fs.copyFileSync(path.join(distAssets, mainJsFile), path.join(assetsDst, 'index.js'));
    console.log(`Updated fallback: assets/index.js (from ${mainJsFile})`);
  }
  if (mainCssFile) {
    fs.copyFileSync(path.join(distAssets, mainCssFile), path.join(assetsDst, 'index.css'));
    console.log(`Updated fallback: assets/index.css (from ${mainCssFile})`);
  }
}

// 2. Read dist/dev.html and write to ./index.html
const distHtml = path.join(dist, 'dev.html');
if (fs.existsSync(distHtml)) {
  const htmlContent = fs.readFileSync(distHtml, 'utf-8');
  fs.writeFileSync(path.join(root, 'index.html'), htmlContent, 'utf-8');
  console.log('Synchronized root production index.html from dist/dev.html');
}

// 3. Ensure favicon.svg, robots.txt, and sitemap.xml in root
const filesToSync = ['favicon.ico', 'favicon.svg', 'robots.txt', 'sitemap.xml', 'logo.svg', 'logo.png', 'apple-touch-icon.png', 'favicon-32x32.png', 'ovd-extension.zip'];
for (const fname of filesToSync) {
  const src = path.join(root, 'public', fname);
  if (fs.existsSync(src)) {
    fs.copyFileSync(src, path.join(root, fname));
    console.log(`Copied root ${fname}`);
  }
}

// 3b. Ensure .well-known files (Apple Pay merchantid verification)
const wellKnownSrc = path.join(root, 'public', '.well-known');
const wellKnownDst = path.join(root, '.well-known');
if (fs.existsSync(wellKnownSrc)) {
  fs.mkdirSync(wellKnownDst, { recursive: true });
  for (const f of fs.readdirSync(wellKnownSrc)) {
    fs.copyFileSync(path.join(wellKnownSrc, f), path.join(wellKnownDst, f));
    console.log(`Copied root .well-known/${f}`);
  }
}

// 4. Ensure .htaccess in root for Hostinger SPA rewrite and caching
const htaccess = `<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\\.html$ - [L]

  # Allow direct access to .well-known files (Apple Pay domain verification, etc.)
  RewriteRule ^\\.well-known/ - [L]

  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>

<FilesMatch "^apple-developer-merchantid-domain-association$">
  ForceType text/plain
  Header set Content-Type "text/plain; charset=utf-8"
</FilesMatch>

<IfModule mod_headers.c>
  <FilesMatch "\\.(html|htm)$">
    Header set Cache-Control "no-cache, no-store, must-revalidate"
    Header set Pragma "no-cache"
    Header set Expires 0
  </FilesMatch>
  <FilesMatch "\\.(js|css)$">
    Header set Cache-Control "public, max-age=31536000, immutable"
  </FilesMatch>
</IfModule>
`;
fs.writeFileSync(path.join(root, '.htaccess'), htaccess, 'utf-8');
console.log('Generated root .htaccess');
