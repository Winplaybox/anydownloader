# OVD PC Worker

YouTube blocks Render's server IP, so YouTube downloads for the Make.com
automation run on your PC (home internet) instead.

Flow: Make → `https://<NGROK_DOMAIN>/download` → yt-dlp on your PC → upload to
OVD `/api/temp-media` → Make posts the returned link to Instagram/Facebook →
OVD deletes the file (or it expires in 6 h).

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

## PC load
One download at a time, below-normal CPU priority, ~40 MB RAM when idle,
temp files deleted after each upload.
