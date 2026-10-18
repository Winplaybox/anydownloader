import fs from 'fs';
import path from 'path';

const root = path.resolve('.');
const dist = path.join(root, 'dist');

// 1. Copy dist/assets/* -> ./assets/*
const assetsDst = path.join(root, 'assets');
fs.mkdirSync(assetsDst, { recursive: true });

const distAssets = path.join(dist, 'assets');
if (fs.existsSync(distAssets)) {
  for (const file of fs.readdirSync(distAssets)) {
    fs.copyFileSync(path.join(distAssets, file), path.join(assetsDst, file));
    console.log(`Copied asset: assets/${file}`);
  }
}

// 2. Production index.html in root for Hostinger auto-deploy
const prodHtml = `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>OVD – Free Online Video, Reel & Audio Downloader</title>
    <meta name="description" content="OVD is a fast and free media downloader. Download High-Definition Videos, YouTube 1080p/4K, Instagram Reels, TikTok without watermark, and MP3 audio in seconds." />
    <meta name="keywords" content="ovd, online video downloader, youtube downloader, instagram reel download, tiktok downloader without watermark, mp3 downloader" />
    <link rel="canonical" href="https://ovd.winplaybox.in/" />
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website" />
    <meta property="og:url" content="https://ovd.winplaybox.in/" />
    <meta property="og:title" content="OVD – Free Online Video, Reel & Audio Downloader" />
    <meta property="og:description" content="Download YouTube 1080p, Instagram Reels, TikTok with no watermark, and high fidelity MP3 audio." />
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script type="module" crossorigin src="/assets/index.js"></script>
    <link rel="stylesheet" crossorigin href="/assets/index.css">
  </head>
  <body class="bg-slate-950 text-slate-100 antialiased selection:bg-rose-500 selection:text-white">
    <div id="root"></div>
  </body>
</html>
`;
fs.writeFileSync(path.join(root, 'index.html'), prodHtml, 'utf-8');
console.log('Generated root production index.html');

// 3. Ensure favicon.svg in root
const favSrc = path.join(root, 'public', 'favicon.svg');
if (fs.existsSync(favSrc)) {
  fs.copyFileSync(favSrc, path.join(root, 'favicon.svg'));
  console.log('Copied root favicon.svg');
}

// 4. Ensure .htaccess in root for Hostinger SPA rewrite and caching
const htaccess = `<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>

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
