// OVD Downloader - Universal In-Page Media Sniffer & Quick Button Injector
// Manifest V3 Content Script — Supports 100% of websites + Dedicated Social Media Optimizers
(function() {
  "use strict";

  const DOWNLOAD_ICON = `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:middle;margin-right:4px;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`;

  function showToast(message, isSuccess = true) {
    const existing = document.querySelector('.ovd-toast-notice');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'ovd-toast-notice';
    toast.innerHTML = `<span style="display:inline-flex;width:8px;height:8px;border-radius:50%;background:${isSuccess ? '#10b981' : '#f43f5e'};margin-right:6px;"></span><span>${message}</span>`;
    document.body.appendChild(toast);
    setTimeout(() => {
      if (toast.parentElement) toast.remove();
    }, 4000);
  }

  function downloadMediaUrl(url, filename = 'ovd_media.mp4') {
    if (!url) return;
    showToast('Starting high-speed download...');
    try {
      chrome.runtime.sendMessage({
        action: 'download_media',
        url: url,
        filename: filename
      }, (resp) => {
        if (chrome.runtime.lastError || !resp || !resp.success) {
          // Direct DOM download fallback
          const a = document.createElement('a');
          a.href = url;
          a.download = filename;
          a.target = '_blank';
          document.body.appendChild(a);
          a.click();
          setTimeout(() => a.remove(), 200);
        }
      });
    } catch (e) {
      window.open(url, '_blank');
    }
  }

  // 1. Popup Listener: Extracts media streams from active page
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'get_page_media') {
      const mediaList = [];
      const hostname = window.location.hostname;

      // Extract HTML5 videos
      document.querySelectorAll('video').forEach((v, idx) => {
        const src = v.currentSrc || v.src || v.querySelector('source')?.src;
        if (src) {
          mediaList.push({
            type: 'video',
            url: src,
            title: document.title || `Video ${idx + 1}`,
            ext: 'mp4'
          });
        }
      });

      // Extract high-res images
      document.querySelectorAll('img').forEach((img, idx) => {
        if (img.src && (img.naturalWidth > 320 || img.clientWidth > 320)) {
          mediaList.push({
            type: 'image',
            url: img.src,
            title: img.alt || `Photo ${idx + 1}`,
            ext: 'jpg'
          });
        }
      });

      sendResponse({
        success: true,
        platform: hostname,
        title: document.title,
        url: window.location.href,
        media: mediaList.slice(0, 10)
      });
    }
    return true;
  });

  // 2. Button Injection Engine: Targeted Social Media + Universal Web Fallback
  function injectButtons() {
    const host = window.location.hostname;

    // --- A. YOUTUBE (Watch & Shorts) ---
    if (host.includes('youtube.com')) {
      if (window.location.pathname.includes('/watch')) {
        const actionsArea = document.querySelector('#top-row.ytd-watch-metadata #actions, #actions.ytd-watch-metadata');
        if (actionsArea && !document.querySelector('#ovd-yt-quick-btn')) {
          const btn = document.createElement('button');
          btn.id = 'ovd-yt-quick-btn';
          btn.className = 'ovd-injected-badge';
          btn.innerHTML = `${DOWNLOAD_ICON}<span>Download (OVD)</span>`;
          btn.onclick = (e) => {
            e.stopPropagation();
            window.open(`https://ovd.winplaybox.in/youtube-video-downloader?url=${encodeURIComponent(window.location.href)}`, '_blank');
          };
          actionsArea.appendChild(btn);
        }
      } else if (window.location.pathname.includes('/shorts/')) {
        const shortsActions = document.querySelector('ytd-reel-player-overlay-renderer #actions, ytd-shorts-player-controls');
        if (shortsActions && !document.querySelector('#ovd-yt-shorts-btn')) {
          const btn = document.createElement('button');
          btn.id = 'ovd-yt-shorts-btn';
          btn.className = 'ovd-injected-badge';
          btn.style.margin = '8px 0';
          btn.innerHTML = `${DOWNLOAD_ICON}<span>Save</span>`;
          btn.onclick = (e) => {
            e.stopPropagation();
            window.open(`https://ovd.winplaybox.in/youtube-video-downloader?url=${encodeURIComponent(window.location.href)}`, '_blank');
          };
          shortsActions.appendChild(btn);
        }
      }
      return;
    }

    // --- B. INSTAGRAM (Reels, Feed & Dialogs) ---
    if (host.includes('instagram.com')) {
      document.querySelectorAll('article video, div[role="dialog"] video, main video, div._aatk video').forEach(v => {
        const card = v.closest('article') || v.closest('div[role="dialog"]') || v.parentElement;
        if (card && !card.querySelector('.ovd-ig-btn')) {
          const btn = document.createElement('button');
          btn.className = 'ovd-floating-action-btn ovd-ig-btn';
          btn.innerHTML = `${DOWNLOAD_ICON}<span>Save Reel (OVD)</span>`;
          btn.onclick = (e) => {
            e.stopPropagation();
            e.preventDefault();
            const src = v.currentSrc || v.src;
            if (src && !src.startsWith('blob:')) {
              downloadMediaUrl(src, `instagram_reel_${Date.now()}.mp4`);
            } else {
              window.open(`https://ovd.winplaybox.in/instagram-reels?url=${encodeURIComponent(window.location.href)}`, '_blank');
            }
          };
          if (getComputedStyle(card).position === 'static') card.style.position = 'relative';
          card.appendChild(btn);
        }
      });
      return;
    }

    // --- C. FACEBOOK (Reels, Videos & Feed) ---
    if (host.includes('facebook.com')) {
      document.querySelectorAll('div[data-pagelet="Reels"], div[role="main"] video, div[role="dialog"] video').forEach(container => {
        const parent = container.closest('div[role="dialog"]') || container.closest('div[data-pagelet="Reels"]') || container.parentElement;
        if (parent && !parent.querySelector('.ovd-fb-btn')) {
          const btn = document.createElement('button');
          btn.className = 'ovd-floating-action-btn ovd-fb-btn';
          btn.innerHTML = `${DOWNLOAD_ICON}<span>Download (OVD)</span>`;
          btn.onclick = (e) => {
            e.stopPropagation();
            e.preventDefault();
            const video = parent.querySelector('video') || container;
            const src = video ? (video.currentSrc || video.src) : null;
            if (src && !src.startsWith('blob:')) {
              downloadMediaUrl(src, `facebook_video_${Date.now()}.mp4`);
            } else {
              window.open(`https://ovd.winplaybox.in/facebook-reels?url=${encodeURIComponent(window.location.href)}`, '_blank');
            }
          };
          if (getComputedStyle(parent).position === 'static') parent.style.position = 'relative';
          parent.appendChild(btn);
        }
      });
      return;
    }

    // --- D. X / TWITTER ---
    if (host.includes('twitter.com') || host.includes('x.com')) {
      document.querySelectorAll('article[data-testid="tweet"]').forEach(tweet => {
        const actionGroup = tweet.querySelector('div[role="group"]');
        if (actionGroup && !tweet.querySelector('.ovd-x-btn')) {
          const btn = document.createElement('button');
          btn.className = 'ovd-injected-badge ovd-x-btn';
          btn.style.marginLeft = '8px';
          btn.innerHTML = `${DOWNLOAD_ICON}<span>Save Media</span>`;
          btn.onclick = (e) => {
            e.stopPropagation();
            e.preventDefault();
            const video = tweet.querySelector('video');
            if (video && (video.currentSrc || video.src)) {
              downloadMediaUrl(video.currentSrc || video.src, `x_video_${Date.now()}.mp4`);
            } else {
              const img = tweet.querySelector('div[data-testid="tweetPhoto"] img');
              if (img && img.src) {
                const origImg = img.src.includes('&name=') ? img.src.replace(/&name=[a-z0-9]+/, '&name=orig') : img.src;
                downloadMediaUrl(origImg, `x_photo_${Date.now()}.jpg`);
              } else {
                window.open(`https://ovd.winplaybox.in/twitter-video-downloader?url=${encodeURIComponent(window.location.href)}`, '_blank');
              }
            }
          };
          actionGroup.appendChild(btn);
        }
      });
      return;
    }

    // --- E. PINTEREST ---
    if (host.includes('pinterest.com')) {
      document.querySelectorAll('div[data-test-id="pin-visual-wrapper"], div[data-test-id="pin"]').forEach(pin => {
        if (!pin.querySelector('.ovd-pin-btn')) {
          const btn = document.createElement('button');
          btn.className = 'ovd-floating-action-btn ovd-pin-btn';
          btn.innerHTML = `${DOWNLOAD_ICON}<span>Save Pin</span>`;
          btn.onclick = (e) => {
            e.stopPropagation();
            e.preventDefault();
            const img = pin.querySelector('img');
            const video = pin.querySelector('video');
            if (video && (video.currentSrc || video.src)) {
              downloadMediaUrl(video.currentSrc || video.src, `pinterest_video_${Date.now()}.mp4`);
            } else if (img && img.src) {
              const origImg = img.src.replace(new RegExp('/\\d+x//'), '/originals/');
              downloadMediaUrl(origImg, `pinterest_image_${Date.now()}.jpg`);
            }
          };
          if (getComputedStyle(pin).position === 'static') pin.style.position = 'relative';
          pin.appendChild(btn);
        }
      });
      return;
    }

    // --- F. UNIVERSAL MEDIA INJECTOR (Any website across the entire web) ---
    document.querySelectorAll('video').forEach((v, idx) => {
      // Ignore hidden or tiny audio trackers
      if (v.offsetWidth < 80 && v.offsetHeight < 80 && !v.clientWidth) return;

      const parent = v.parentElement;
      if (!parent || parent.querySelector('.ovd-universal-video-badge')) return;

      if (getComputedStyle(parent).position === 'static') {
        parent.style.position = 'relative';
      }

      const btn = document.createElement('button');
      btn.className = 'ovd-universal-video-badge';
      btn.innerHTML = `${DOWNLOAD_ICON}<span>Download Video</span>`;
      btn.onclick = (e) => {
        e.stopPropagation();
        e.preventDefault();
        const src = v.currentSrc || v.src || v.querySelector('source')?.src;
        if (src && !src.startsWith('blob:')) {
          const cleanName = (document.title || 'video').replace(/[^a-zA-Z0-9_-]/g, '_').substring(0, 30);
          downloadMediaUrl(src, `${cleanName}_${Date.now()}.mp4`);
        } else {
          window.open(`https://ovd.winplaybox.in/?url=${encodeURIComponent(window.location.href)}`, '_blank');
        }
      };
      parent.appendChild(btn);
    });

    // Universal High-Res Image Overlay on Hover
    document.querySelectorAll('img').forEach(img => {
      if ((img.naturalWidth > 350 || img.clientWidth > 350) && !img.dataset.ovdBound) {
        img.dataset.ovdBound = 'true';
        const parent = img.parentElement;
        if (!parent || parent.querySelector('.ovd-universal-img-badge')) return;

        parent.classList.add('ovd-img-container');
        if (getComputedStyle(parent).position === 'static') {
          parent.style.position = 'relative';
        }

        const btn = document.createElement('button');
        btn.className = 'ovd-universal-img-badge';
        btn.innerHTML = `${DOWNLOAD_ICON}<span>Save</span>`;
        btn.onclick = (e) => {
          e.stopPropagation();
          e.preventDefault();
          const cleanName = (img.alt || document.title || 'photo').replace(/[^a-zA-Z0-9_-]/g, '_').substring(0, 30);
          downloadMediaUrl(img.src, `${cleanName}_${Date.now()}.jpg`);
        };
        parent.appendChild(btn);
      }
    });
  }

  // Run on load and observe DOM changes
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectButtons);
  } else {
    injectButtons();
  }

  let rafScheduled = false;
  const observer = new MutationObserver(() => {
    if (!rafScheduled) {
      rafScheduled = true;
      requestAnimationFrame(() => {
        injectButtons();
        rafScheduled = false;
      });
    }
  });

  observer.observe(document.body || document.documentElement, {
    childList: true,
    subtree: true
  });

  // Also periodic safety pulse for dynamic infinite scroll feeds
  setInterval(injectButtons, 2000);

})();
