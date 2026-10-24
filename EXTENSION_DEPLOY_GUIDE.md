# OVD Chrome Extension — Deployment & Web Store Guide

## 1. Extension Files & Archive
- **Source Directory:** `extension/`
- **Ready-to-Deploy ZIP:** `ovd-extension.zip` (available in project root and at `https://ovd.winplaybox.in/ovd-extension.zip`)
- **Manifest:** Manifest V3 (`extension/manifest.json`)
- **Icons:** 16x16, 48x48, 128x128 (`extension/icons/`)

---

## 2. Test Unpacked Extension Locally (Takes 30 Seconds)

1. Open Google Chrome and navigate to: `chrome://extensions/`
2. Enable **Developer mode** toggle in the top-right corner.
3. Click **Load unpacked** in the top-left corner.
4. Select the `extension` directory from this project (`C:\Users\sagar\Desktop\Project\anydownloader\extension`).
5. The **OVD Downloader PRO** extension icon will appear in your Chrome toolbar!

---

## 3. How to Deploy to Google Chrome Web Store

### Step 1: Open Chrome Developer Dashboard
1. Go to [https://chrome.google.com/webstore/devconsole/](https://chrome.google.com/webstore/devconsole/).
2. Sign in with your Google account.
3. Pay the one-time $5 Google Developer registration fee (if first time).

### Step 2: Upload the Extension Package
1. Click the **+ New Item** button.
2. Drag and drop or browse to select `ovd-extension.zip`.
3. The dashboard will automatically parse `manifest.json`.

### Step 3: Complete the Store Listing
- **Item Name:** `OVD Downloader PRO - Video & Audio Saver`
- **Summary:** `Download 1080p/4K YouTube videos, Instagram Reels, Facebook videos, Twitter/X media, and TikToks in 1-click.`
- **Category:** `Productivity` or `Photos & Video`
- **Language:** `English`
- **Icon:** Upload `extension/icons/icon128.png` (128x128).
- **Screenshots:** Upload at least one 1280x800 screenshot showing the popup downloading a video.

### Step 4: Privacy Practices Form
Chrome Web Store requires privacy justifications for permissions:
- **Single Purpose Description:**
  > "Allows users to extract and download public and user-authorized videos, reels, and audio tracks for offline viewing."
- **Permission Justifications:**
  - `activeTab`: Detects if the current webpage is a supported media site (YouTube, Instagram, TikTok, Facebook, Twitter).
  - `downloads`: Saves the extracted video or MP3 file directly to the user's local Downloads folder.
  - `storage`: Remembers the user's preferred quality setting (e.g. 1080p vs 720p).
- **Privacy Policy URL:** `https://ovd.winplaybox.in/privacy`
- **Data Usage:** Select: *"This extension does not collect, sell, or transfer any user personal data to third parties."*

### Step 5: Submit for Review
Click **Submit for Review**. Chrome Web Store reviews typically take 24–48 hours, after which your extension will be publicly live and installable worldwide!
