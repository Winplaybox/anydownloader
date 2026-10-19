// OVD Downloader PRO - Background Service Worker

const EXTENSION_KEY = 'wpb_ext_9f83e2a74c1048b9ad51f63cb7e90812';

chrome.runtime.onInstalled.addListener(() => {
  // Context menus for quick right-click download
  chrome.contextMenus.create({
    id: "ovd-download-link",
    title: "Download with OVD Downloader PRO",
    contexts: ["link", "video", "image", "page"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "ovd-download-link") {
    const targetUrl = info.srcUrl || info.linkUrl || (tab && tab.url);
    if (targetUrl) {
      const ovdUrl = `https://ovd.winplaybox.in/?url=${encodeURIComponent(targetUrl)}`;
      chrome.tabs.create({ url: ovdUrl });
    }
  }
});

// Direct High-Speed Download Manager for Content Script & Popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'download_media') {
    const url = request.url;
    let filename = request.filename || 'ovd_download.mp4';
    // Clean filename
    filename = filename.replace(/[\\/*?:\"<>|]/g, '_');

    try {
      chrome.downloads.download({
        url: url,
        filename: filename,
        saveAs: false,
        conflictAction: 'uniquify'
      }, (downloadId) => {
        if (chrome.runtime.lastError) {
          sendResponse({ success: false, error: chrome.runtime.lastError.message });
        } else {
          sendResponse({ success: true, downloadId: downloadId });
        }
      });
    } catch (err) {
      sendResponse({ success: false, error: err.message });
    }
    return true; // Keep message channel open for async response
  }

  if (request.action === 'get_auth_key') {
    sendResponse({ key: EXTENSION_KEY });
    return true;
  }
});
