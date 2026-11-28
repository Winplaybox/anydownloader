# OVD PC Worker

YouTube blocks Render's server IP, so YouTube downloads for the Make.com
automation run on your PC (home internet) instead.

The Telegram bot and other callers send `POST /download` with
`{"url":"…","kind":"video","height":1080}` and either `X-Worker-Key` or
`Authorization: Bearer <key>`. The worker runs yt-dlp on YouTube, Instagram,
and the existing supported platforms. It returns `{"ok":true,"url":"…"}`;
fetch that URL without the worker key. It expires after 15 minutes or when
the worker restarts. A busy worker returns HTTP 429.

## One-time setup (Windows)
1. Install Python 3.11+ (python.org, tick "Add to PATH").
2. Install ngrok: `winget install ngrok.ngrok`, sign up free at ngrok.com, then
   `ngrok config add-authtoken <your token>`.
3. ngrok dashboard → **Domains** → claim your free static domain.
4. Put this folder somewhere permanent, e.g. `C:\OVD-Worker`, with `worker.env`
   next to `start_worker.bat`. Set `NGROK_DOMAIN` in `worker.env`.
5. Double-click `start_worker.bat` (first run installs everything).

## Start with Windows
`Win + R` → `shell:startup` → create a shortcut to `start_worker.bat` there.

## Check it
Open `https://<NGROK_DOMAIN>/health` — expect `{"ok": true, ...}`.

## Serving files
Set `WORKER_PUBLIC_BASE_URL` when the public address differs from the ngrok
domain or `https://worker.winplaybox.in`. Use `http://127.0.0.1:8787` for
same-host callers. A reverse proxy must forward `/download-files/*` (including
the query string) to the worker, not serve that path from disk. Avoid logging
the query string on this route: it contains the file access signature.

The worker stores files outside the web root, in `WORKER_MEDIA_DIR` or a private
directory under the system temp directory. Do not expose it through static
hosting. The old `STATIC_*` and `OVD_API_KEY`/`OVD_BASE` settings are no longer
used by this worker. Remove any old static files after switching.
If needed, set `COOKIES_FILE` to a server-side Netscape cookie file; never put
that file in the media directory or include it in a request.

## PC load
One download at a time, below-normal CPU priority, ~40 MB RAM when idle.
Scratch files are removed after each download; expired results are purged every minute.
