// OVD Downloader PRO - Background Service Worker

chrome.runtime.onInstalled.addListener(() => {
  // Add right-click context menu
  chrome.contextMenus.create({
    id: "ovd-download-media",
    title: "Download with OVD Downloader PRO",
    contexts: ["link", "video", "page"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "ovd-download-media") {
    const targetUrl = info.linkUrl || info.srcUrl || info.pageUrl || (tab && tab.url);
    if (targetUrl) {
      const ovdUrl = `https://ovd.winplaybox.in/?url=${encodeURIComponent(targetUrl)}`;
      chrome.tabs.create({ url: ovdUrl });
    }
  }
});
