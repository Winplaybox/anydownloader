// OVD Downloader - Popup Controller
const BACKEND_URL = 'https://anydownloader-backend-vvbj.onrender.com';
const EXTENSION_KEY = 'wpb_ext_9f83e2a74c1048b9ad51f63cb7e90812';

document.addEventListener('DOMContentLoaded', async () => {
 const platformBanner = document.getElementById('platform-banner');
 const platformIcon = document.getElementById('platform-icon');
 const platformTitle = document.getElementById('platform-title');
 const platformSubtitle = document.getElementById('platform-subtitle');
 const platformBadge = document.getElementById('platform-badge');
 const featureChips = document.getElementById('feature-chips');
 const detectedBox = document.getElementById('detected-box');
 const detectedItems = document.getElementById('detected-items');
 const urlInput = document.getElementById('url-input');
 const detectedTag = document.getElementById('detected-tag');
 const fetchBtn = document.getElementById('fetch-btn');
 const statusEl = document.getElementById('status');
 const resultBox = document.getElementById('result-box');
 const resultTitle = document.getElementById('result-title');
 const resultButtons = document.getElementById('result-buttons');

 let activeTab = null;

 // 1. Detect Active Tab Platform
 try {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  activeTab = tab;
  if (tab && tab.url) {
   urlInput.value = tab.url;
   detectedTag.innerText = 'Active Tab URL';
   configurePlatformUI(tab.url);

   // Probe active tab for in-page media streams (decrypted from DOM!)
   chrome.tabs.sendMessage(tab.id, { action: 'get_page_media' }, (res) => {
    if (!chrome.runtime.lastError && res && res.media && res.media.length > 0) {
     showDetectedMedia(res.media);
    }
   });
  }
 } catch (err) {
  console.error('Tab query error:', err);
 }

 // Configure UI dynamically based on detected platform
 function configurePlatformUI(url) {
  featureChips.innerHTML = '';

  if (url.includes('facebook.com')) {
   platformBanner.className = 'platform-banner fb';
   platformIcon.innerText = '📘';
   platformTitle.innerText = 'Facebook Detected';
   platformSubtitle.innerText = 'Reels, Feed Videos, Stories & Photos';
   platformBadge.innerText = 'FB MODE';

   addChip('Reels Downloader', 'https://ovd.winplaybox.in/facebook-reels');
   addChip('Feed Videos', 'https://ovd.winplaybox.in/facebook-video-downloader');
   addChip('FB Posts & Photos', 'https://ovd.winplaybox.in/facebook-posts');
   addChip('Top 100 Pages', 'https://ovd.winplaybox.in/facebook/top-100-facebook-pages');

  } else if (url.includes('instagram.com')) {
   platformBanner.className = 'platform-banner ig';
   platformIcon.innerText = '📸';
   platformTitle.innerText = 'Instagram Detected';
   platformSubtitle.innerText = 'Reels, Stories, Carousel & Photos';
   platformBadge.innerText = 'IG MODE';

   addChip('Reels Saver', 'https://ovd.winplaybox.in/instagram-reels');
   addChip('Photos & Carousel', 'https://ovd.winplaybox.in/instagram-photos');
   addChip('Stories', 'https://ovd.winplaybox.in/instagram-stories');
   addChip('Top 100 Accounts', 'https://ovd.winplaybox.in/instagram/top-100-instagram-accounts');

  } else if (url.includes('twitter.com') || url.includes('x.com')) {
   platformBanner.className = 'platform-banner tw';
   platformIcon.innerText = '🐦';
   platformTitle.innerText = 'X (Twitter) Detected';
   platformSubtitle.innerText = '1080p MP4, 320k MP3, HD Images & GIFs';
   platformBadge.innerText = 'X MODE';

   addChip('Tweet MP4 Video', 'https://ovd.winplaybox.in/twitter-video-downloader');
   addChip('Tweet to MP3', 'https://ovd.winplaybox.in/twitter-mp3');
   addChip('HD Image Saver', 'https://ovd.winplaybox.in/twitter-images');
   addChip('Animated GIFs', 'https://ovd.winplaybox.in/twitter-gifs');

  } else if (url.includes('pinterest.com')) {
   platformBanner.className = 'platform-banner pin';
   platformIcon.innerText = '📌';
   platformTitle.innerText = 'Pinterest Detected';
   platformSubtitle.innerText = 'HD Image Pins, Video Pins & Boards';
   platformBadge.innerText = 'PIN MODE';

   addChip('HD Photo Pin', 'https://ovd.winplaybox.in/pinterest/pinterest-images');
   addChip('Video Pin', 'https://ovd.winplaybox.in/pinterest/pinterest-video-downloader');
   addChip('Board Saver', 'https://ovd.winplaybox.in/pinterest/pinterest-board-downloader');
   addChip('DP Avatar', 'https://ovd.winplaybox.in/pinterest/pinterest-profile-downloader');

  } else if (url.includes('youtube.com')) {
   platformBanner.className = 'platform-banner yt';
   platformIcon.innerText = '▶️';
   platformTitle.innerText = 'YouTube Detected';
   platformSubtitle.innerText = '1080p / 4K MP4, 320kbps MP3 & Shorts';
   platformBadge.innerText = 'YT MODE';

   addChip('1080p MP4', 'https://ovd.winplaybox.in/youtube-mp4');
   addChip('320k MP3', 'https://ovd.winplaybox.in/youtube-mp3');
   addChip('Shorts Saver', 'https://ovd.winplaybox.in/youtube-shorts');
   addChip('Top 100 Channels', 'https://ovd.winplaybox.in/youtube/top-100-youtube-channels');

  } else {
   platformBanner.className = 'platform-banner';
   platformIcon.innerText = '🌐';
   platformTitle.innerText = 'Universal Media Sniffer';
   platformSubtitle.innerText = 'Extract videos & audio from any web page';
   platformBadge.innerText = 'READY';

   addChip('YouTube Suite', 'https://ovd.winplaybox.in/youtube-video-downloader');
   addChip('Facebook Suite', 'https://ovd.winplaybox.in/facebook-reels');
   addChip('Instagram Suite', 'https://ovd.winplaybox.in/instagram-reels');
   addChip('X / Twitter Suite', 'https://ovd.winplaybox.in/twitter-video-downloader');
  }
 }

 function addChip(label, link) {
  const a = document.createElement('a');
  a.className = 'chip';
  a.href = link;
  a.target = '_blank';
  a.innerText = label;
  featureChips.appendChild(a);
 }

 function showDetectedMedia(mediaList) {
  detectedBox.style.display = 'block';
  detectedItems.innerHTML = '';

  mediaList.forEach((item, idx) => {
   const btn = document.createElement('div');
   btn.className = 'detected-item-btn';
   const label = item.type === 'video' ? `🎬 ${item.title.slice(0, 32)} (MP4)` : `🖼 ${item.title.slice(0, 32)} (HD)`;
   btn.innerHTML = `<span>${label}</span><span style="color:#10b981;">&#10515; Save</span>`;
   btn.onclick = () => {
    btn.innerText = 'Downloading...';
    chrome.runtime.sendMessage({
     action: 'download_media',
     url: item.url,
     filename: `ovd_saved_${Date.now()}.${item.ext || 'mp4'}`
    }, () => {
     btn.innerHTML = `<span>${label}</span><span style="color:#38bdf8;">&#10003; Saved!</span>`;
    });
   };
   detectedItems.appendChild(btn);
  });
 }

 // 2. Fetch Media Handler via API
 fetchBtn.addEventListener('click', async () => {
  const rawUrl = urlInput.value.trim();
  if (!rawUrl) {
   statusEl.className = 'status-msg status-error';
   statusEl.innerText = 'Please enter a valid media link.';
   return;
  }

  statusEl.className = 'status-msg status-info';
  statusEl.innerText = 'Fetching download streams with authorized key...';
  fetchBtn.disabled = true;
  resultBox.style.display = 'none';
  resultButtons.innerHTML = '';

  try {
   const resp = await fetch(`${BACKEND_URL}/api/extract`, {
    method: 'POST',
    headers: {
     'Content-Type': 'application/json',
     'X-Extension-Key': EXTENSION_KEY
    },
    body: JSON.stringify({ url: rawUrl })
   });

   const res = await resp.json();
   if (!res.success || !res.data) {
    throw new Error(res.error || 'Could not extract streams. Please try on OVD Web.');
   }

   const data = res.data;
   statusEl.innerText = '';
   resultBox.style.display = 'block';
   resultTitle.innerText = data.title || 'Extracted Media';

   // Video formats
   if (data.video_formats && data.video_formats.length > 0) {
    data.video_formats.slice(0, 3).forEach(fmt => {
     const btn = document.createElement('button');
     btn.className = 'download-btn mp4';
     btn.innerHTML = `<span>🎬 ${fmt.quality || 'Video'} (${fmt.ext || 'MP4'})</span><span>&#10515; Download</span>`;
     btn.onclick = () => {
      const dlUrl = fmt.stream_url.startsWith('http') ? fmt.stream_url : `${BACKEND_URL}${fmt.stream_url}`;
      chrome.runtime.sendMessage({
       action: 'download_media',
       url: dlUrl,
       filename: fmt.download_name || 'video.mp4'
      });
     };
     resultButtons.appendChild(btn);
    });
   }

   // Audio format
   if (data.audio_formats && data.audio_formats.length > 0) {
    const audio = data.audio_formats[0];
    const btn = document.createElement('button');
    btn.className = 'download-btn mp3';
    btn.innerHTML = `<span>🎵 Audio Track (${audio.quality || '320kbps MP3'})</span><span>&#10515; Save</span>`;
    btn.onclick = () => {
     const dlUrl = audio.stream_url.startsWith('http') ? audio.stream_url : `${BACKEND_URL}${audio.stream_url}`;
     chrome.runtime.sendMessage({
      action: 'download_media',
      url: dlUrl,
      filename: audio.download_name || 'audio.mp3'
     });
    };
    resultButtons.appendChild(btn);
   }

   // Thumbnails
   if (data.thumbnails && data.thumbnails.length > 0) {
    const thumb = data.thumbnails[0];
    const btn = document.createElement('button');
    btn.className = 'download-btn photo';
    btn.innerHTML = `<span>🖼 Full-Res Cover / Artwork</span><span>&#10515; Save</span>`;
    btn.onclick = () => {
     const dlUrl = thumb.stream_url.startsWith('http') ? thumb.stream_url : `${BACKEND_URL}${thumb.stream_url}`;
     chrome.runtime.sendMessage({
      action: 'download_media',
      url: dlUrl,
      filename: 'cover.jpg'
     });
    };
    resultButtons.appendChild(btn);
   }

   // Open in OVD Web
   const webBtn = document.createElement('a');
   webBtn.className = 'download-btn';
   webBtn.href = `https://ovd.winplaybox.in/?url=${encodeURIComponent(rawUrl)}`;
   webBtn.target = '_blank';
   webBtn.innerHTML = `<span>🌐 Open Player on OVD Web</span><span>&rarr;</span>`;
   resultButtons.appendChild(webBtn);

  } catch (err) {
   statusEl.className = 'status-msg status-error';
   statusEl.innerText = err.message || 'Extraction error. Try opening on OVD web.';
  } finally {
   fetchBtn.disabled = false;
  }
 });
});
