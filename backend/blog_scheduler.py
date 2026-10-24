import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
ARTICLES_FILE = os.path.join(DATA_DIR, "articles.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "blog_settings.json")

DEFAULT_SETTINGS = {
    "frequency": "daily",
    "auto_publish": True,
    "last_run": None,
    "target_platforms": ["YouTube", "Instagram", "TikTok", "Facebook", "Twitter", "Reddit"],
    "content_focus": "Download guides, creator algorithms, video quality optimization, and audio extraction"
}

TOPIC_TEMPLATES = [
    {
        "title": "Instagram Reels 2026 Strategy: How to Save and Repurpose 1080p Content Without Quality Loss",
        "platform": "Instagram",
        "category": "Creator Strategy",
        "readTime": "4 min read",
        "summary": "Learn how Instagram's latest H.265 CDN encoding impacts video clarity and how creators can extract and preserve maximum bitrate for cross-posting.",
        "image": "https://images.unsplash.com/photo-1611162616305-c69b3fa7fbe0?w=800&auto=format&fit=crop&q=80",
        "content": """### Instagram's 2026 Compression Architecture
Instagram processes millions of vertical reels daily using variable bitrate encoding. For creators repurposing content across platforms, downloading compressed feed video can introduce compression artifacts.

### Key Insights for Content Preservation:
1. **Download Pre-Transcode Formats**: Always extract original resolution (1080x1920) before secondary platform downsampling.
2. **Audio Sync Guarantees**: Separately extracted high-fidelity audio ensures zero pitch distortion when re-editing.
3. **Hashtag & Caption Preservation**: Extracting the exact metadata helps maintain search visibility when archiving top posts.
"""
    },
    {
        "title": "YouTube 4K & 1080p60 Video Extraction: Understanding Container Formats (MP4 vs WebM)",
        "platform": "YouTube",
        "category": "Technical Guide",
        "readTime": "5 min read",
        "summary": "A deep dive into why YouTube streams high-resolution video and audio on separate tracks, and how ffmpeg merging delivers pristine universal files.",
        "image": "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=800&auto=format&fit=crop&q=80",
        "content": """### The Evolution of YouTube Adaptive Streaming (DASH)
Since 2020, YouTube does not serve 1080p, 1440p, or 4K videos as single monolithic files. Instead, it serves adaptive video streams (often using VP9 or AV1 codecs) completely separate from the audio stream (Opus/AAC).

### Why Merging is Essential:
- **Audio Synchronization**: Merging combines the highest bitrate video stream with the best audio track into a standard H.264 MP4 container.
- **Offline Playback**: Standard media players and smart TVs require synchronized containers to prevent audio lag.
- **Universal Compatibility**: MP4 container files work out-of-the-box on iPhone, Android, Windows, and macOS without additional codecs.
"""
    },
    {
        "title": "TikTok Audio & Slideshow Extraction: Bypassing Watermarks Safely in 2026",
        "platform": "TikTok",
        "category": "Audio & Media",
        "readTime": "3 min read",
        "summary": "How TikTok creators extract original music tracks, multi-photo carousels, and watermark-free clips for backup and offline listening.",
        "image": "https://images.unsplash.com/photo-1596558450255-7c0b7be9d56a?w=800&auto=format&fit=crop&q=80",
        "content": """### TikTok's Native Watermark Mechanism
TikTok injects bouncing watermarks and ending cards directly into the rendered video on device. However, the raw source video uploaded by the creator resides on ByteDance CDN servers without watermarks.

### Extraction Best Practices:
1. **Direct CDN Resolution**: Tools like TikWM query the unbranded content stream directly from server nodes.
2. **Slideshow Carousels**: Photo posts are delivered as discrete high-resolution JPEG images accompanied by an MP3 audio track.
3. **Soundtrack Preservation**: Extracting the original sound track enables creators to identify viral trends before they peak.
"""
    }
]

class BlogScheduler:
    def __init__(self):
        self.settings = self._load_settings()
        self.articles = self._load_articles()

    def _load_settings(self) -> Dict[str, Any]:
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return dict(DEFAULT_SETTINGS)

    def _save_settings(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2)

    def _load_articles(self) -> List[Dict[str, Any]]:
        if os.path.exists(ARTICLES_FILE):
            try:
                with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_articles(self):
        with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.articles, f, indent=2)

    def get_settings(self) -> Dict[str, Any]:
        return self.settings

    def update_settings(self, new_settings: Dict[str, Any]) -> Dict[str, Any]:
        self.settings.update(new_settings)
        self._save_settings()
        return self.settings

    def get_articles(self) -> List[Dict[str, Any]]:
        return self.articles

    def generate_daily_article(self, force: bool = False) -> Dict[str, Any]:
        """Generates a scheduled article autonomously based on active settings."""
        today = datetime.now().strftime("%Y-%m-%d")
        if not force and self.settings.get("last_run") == today:
            return {"ok": True, "message": "Article already generated today", "skipped": True}

        # Pick topic based on current article count
        idx = len(self.articles) % len(TOPIC_TEMPLATES)
        template = dict(TOPIC_TEMPLATES[idx])

        article_id = f"{template['platform'].lower()}-{int(time.time())}"
        template["id"] = article_id
        template["slug"] = f"{template['platform'].lower()}-guide-{int(time.time())}"
        template["date"] = datetime.now().strftime("%b %d, %Y")
        template["publishedAt"] = datetime.now().isoformat()
        template["autonomous"] = True

        self.articles.insert(0, template)
        self._save_articles()

        self.settings["last_run"] = today
        self._save_settings()

        return {"ok": True, "article": template}

blog_scheduler = BlogScheduler()
