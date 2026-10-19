// OVD Downloader PRO - In-page Quick Button Injector
(function() {
  function injectOvdButton() {
    // 1. YouTube watch page
    if (window.location.hostname.includes('youtube.com') && window.location.pathname.includes('/watch')) {
      const actionsArea = document.querySelector('#top-row.ytd-watch-metadata #actions');
      if (actionsArea && !document.querySelector('#ovd-yt-quick-btn')) {
        const btn = document.createElement('button');
        btn.id = 'ovd-yt-quick-btn';
        btn.innerHTML = '⚡ Download with OVD';
        btn.style.cssText = 'background: linear-gradient(135deg, #e11d48, #ec4899); color: #fff; font-weight: bold; font-size: 12px; border: none; border-radius: 18px; padding: 8px 14px; margin-left: 8px; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; box-shadow: 0 4px 12px rgba(225, 29, 72, 0.3); z-index: 9999;';
        btn.addEventListener('click', () => {
          window.open(`https://ovd.winplaybox.in/?url=${encodeURIComponent(window.location.href)}`, '_blank');
        });
        actionsArea.appendChild(btn);
      }
    }

    // 2. Instagram Reels / Posts
    if (window.location.hostname.includes('instagram.com') && (window.location.pathname.includes('/reel/') || window.location.pathname.includes('/p/'))) {
      if (!document.querySelector('#ovd-ig-floating-btn')) {
        const btn = document.createElement('div');
        btn.id = 'ovd-ig-floating-btn';
        btn.innerHTML = '⚡ Download Media (OVD)';
        btn.style.cssText = 'position: fixed; bottom: 24px; right: 24px; background: linear-gradient(135deg, #ec4899, #8b5cf6); color: #fff; font-family: -apple-system, sans-serif; font-weight: bold; font-size: 13px; border-radius: 24px; padding: 10px 18px; cursor: pointer; z-index: 99999; box-shadow: 0 6px 20px rgba(236, 72, 153, 0.4); display: flex; align-items: center; gap: 6px;';
        btn.addEventListener('click', () => {
          window.open(`https://ovd.winplaybox.in/?url=${encodeURIComponent(window.location.href)}`, '_blank');
        });
        document.body.appendChild(btn);
      }
    }
  }

  setInterval(injectOvdButton, 2000);
})();
