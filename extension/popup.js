// OVD Downloader PRO - Popup Script
const BACKEND_URL = 'https://anydownloader-backend-vvbj.onrender.com';

document.addEventListener('DOMContentLoaded', async () => {
  const urlInput = document.getElementById('url-input');
  const fetchBtn = document.getElementById('fetch-btn');
  const statusEl = document.getElementById('status');
  const resultBox = document.getElementById('result-box');
  const resultTitle = document.getElementById('result-title');
  const resultButtons = document.getElementById('result-buttons');
  const detectedTag = document.getElementById('detected-tag');

  // 1. Automatically grab active tab URL
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab && tab.url && (tab.url.includes('youtube.com') || tab.url.includes('instagram.com') || tab.url.includes('facebook.com') || tab.url.includes('tiktok.com'))) {
      urlInput.value = tab.url;
      detectedTag.innerText = 'Detected from active tab';
    } else {
      detectedTag.innerText = '';
    }
  } catch (e) {
    detectedTag.innerText = '';
  }

  // 2. Fetch Media Handler
  fetchBtn.addEventListener('click', async () => {
    const rawUrl = urlInput.value.trim();
    if (!rawUrl) {
      statusEl.className = 'status-msg status-error';
      statusEl.innerText = 'Please paste a valid video or photo link.';
      return;
    }

    statusEl.className = 'status-msg status-info';
    statusEl.innerText = 'Fetching download streams from engine...';
    fetchBtn.disabled = true;
    resultBox.style.display = 'none';
    resultButtons.innerHTML = '';

    try {
      const resp = await fetch(`${BACKEND_URL}/api/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: rawUrl })
      });

      const res = await resp.json();
      if (!res.success || !res.data) {
        throw new Error(res.error || 'Could not parse media from URL.');
      }

      const data = res.data;
      statusEl.innerText = '';
      resultBox.style.display = 'block';
      resultTitle.innerText = data.title || 'Extracted Media';

      // 1. Video formats
      if (data.video_formats && data.video_formats.length > 0) {
        data.video_formats.slice(0, 3).forEach(fmt => {
          const a = document.createElement('a');
          a.className = 'download-btn mp4';
          a.href = `${BACKEND_URL}${fmt.stream_url}`;
          a.target = '_blank';
          a.innerHTML = `<span>🎬 ${fmt.quality || 'Video'} (${fmt.ext || 'MP4'})</span><span>Download &darr;</span>`;
          resultButtons.appendChild(a);
        });
      }

      // 2. Audio format (MP3)
      if (data.audio_formats && data.audio_formats.length > 0) {
        const bestAudio = data.audio_formats[0];
        const a = document.createElement('a');
        a.className = 'download-btn mp3';
        a.href = `${BACKEND_URL}${bestAudio.stream_url}`;
        a.target = '_blank';
        a.innerHTML = `<span>🎵 Audio Track (${bestAudio.ext || 'MP3'})</span><span>Download &darr;</span>`;
        resultButtons.appendChild(a);
      }

      // 3. Thumbnails / Photo
      if (data.thumbnails && data.thumbnails.length > 0) {
        const bestThumb = data.thumbnails[0];
        const a = document.createElement('a');
        a.className = 'download-btn photo';
        a.href = `${BACKEND_URL}${bestThumb.stream_url}`;
        a.target = '_blank';
        a.innerHTML = `<span>🖼️ High-Res Image / Cover</span><span>Download &darr;</span>`;
        resultButtons.appendChild(a);
      }

      // 4. Fallback link to open in web
      const webLink = document.createElement('a');
      webLink.className = 'download-btn';
      webLink.href = `https://ovd.winplaybox.in/?url=${encodeURIComponent(rawUrl)}`;
      webLink.target = '_blank';
      webLink.innerHTML = `<span>🌐 Open Full Player on OVD Web</span><span>Open &rarr;</span>`;
      resultButtons.appendChild(webLink);

    } catch (err) {
      statusEl.className = 'status-msg status-error';
      statusEl.innerText = err.message || 'Engine connection error. Try opening in OVD web.';
    } finally {
      fetchBtn.disabled = false;
    }
  });
});
