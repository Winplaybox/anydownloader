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
    "target_platforms": ["YouTube", "Instagram", "TikTok", "Facebook", "Twitter", "Reddit", "Pinterest", "Threads"],
    "content_focus": "Download guides, creator algorithms, video quality optimization, and audio extraction"
}

TOPIC_TEMPLATES = [
    {
        "title": "How to Download Instagram Reels in 1080p HD with Audio: 2026 Creator Guide",
        "platform": "Instagram",
        "category": "Instagram Guides",
        "readTime": "4 min read",
        "summary": "Learn how Instagram's CDN encoding affects video clarity and how creators can extract and preserve maximum bitrate for cross-posting without compression artifacts.",
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
        "title": "Save TikTok Videos Without Watermark: The Complete Free Guide",
        "platform": "TikTok",
        "category": "TikTok Guides",
        "readTime": "3 min read",
        "summary": "Step-by-step method to download original TikTok MP4 videos without the bouncing logo, plus how to extract viral background music tracks.",
        "image": "https://images.unsplash.com/photo-1596558450255-7c0b7be9d56a?w=800&auto=format&fit=crop&q=80",
        "content": """### TikTok's Native Watermark Mechanism
TikTok injects bouncing watermarks and ending cards directly into the rendered video on device. However, the raw source video uploaded by the creator resides on ByteDance CDN servers without watermarks.

### Extraction Best Practices:
1. **Direct CDN Resolution**: Tools like OVD Downloader query the unbranded content stream directly from server nodes.
2. **Slideshow Carousels**: Photo posts are delivered as discrete high-resolution JPEG images accompanied by an MP3 audio track.
3. **Soundtrack Preservation**: Extracting the original sound track enables creators to identify viral trends before they peak.
"""
    },
    {
        "title": "How to Save Twitter (X) Videos & GIFs to Camera Roll in Full HD",
        "platform": "Twitter",
        "category": "Twitter / X",
        "readTime": "4 min read",
        "summary": "A comprehensive guide on extracting high-bitrate MP4 videos and animated GIFs from Twitter/X threads without screen recording.",
        "image": "https://images.unsplash.com/photo-1611605698335-8b1569810432?w=800&auto=format&fit=crop&q=80",
        "content": """### How Twitter/X Handles Media Streams
Twitter encodes video uploads into multiple progressive MP4 renditions ranging from 360p up to 1080p, while converting all animated GIFs into looping H.264 video files.

### Why Direct Extraction Beats Screen Recording:
- **Pristine Quality**: Direct stream downloads preserve 100% of the original color grading and bitrates (up to 4.5 Mbps).
- **Exact Aspect Ratios**: Avoid black letterbox bars caused by mobile screen recorders.
- **Clean Audio**: Screen recorders capture phone notifications and microphone noise; direct extraction pulls the digital audio stream.
"""
    },
    {
        "title": "Fix Reddit Video Audio Sync: How to Merge Reddit DASH Video and Sound",
        "platform": "Reddit",
        "category": "Reddit Guides",
        "readTime": "4 min read",
        "summary": "Why Reddit videos download without sound when using standard browser save options, and how OVD automatically merges DASH tracks using ffmpeg.",
        "image": "https://images.unsplash.com/photo-1543269865-cbf427effbad?w=800&auto=format&fit=crop&q=80",
        "content": """### Why Reddit Videos Download Without Sound
Reddit utilizes MPEG-DASH (Dynamic Adaptive Streaming over HTTP). The video stream (v.redd.it/video) and the audio stream (v.redd.it/audio) are hosted as completely separate URLs to adapt to changing network conditions.

### How OVD Downloader Solves DASH Separation:
1. **Parallel Extraction**: OVD fetches both the highest-quality video stream and the lossless AAC audio stream.
2. **Server-Side FFmpeg Merging**: Merges both streams into a single standard MP4 container in milliseconds.
3. **Instant Device Delivery**: You receive a fully synchronized, ready-to-share MP4 file.
"""
    },
    {
        "title": "Pinterest Video Pin Downloader: How to Save 4K Pins and High-Res Images",
        "platform": "Pinterest",
        "category": "Pinterest Guides",
        "readTime": "3 min read",
        "summary": "How designers and creators save inspiration boards, animated video pins, and ultra-high resolution photography from Pinterest.",
        "image": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&auto=format&fit=crop&q=80",
        "content": """### Unlocking Full-Resolution Media on Pinterest
Pinterest displays compressed thumbnails in its grid feed to conserve bandwidth. The original uncompressed assets are buried in the pin's JSON schema metadata.

### How to Retrieve True Uncompressed Pins:
- **Bypass 736x Thumbnails**: OVD inspects the source schema to locate `originals/` image paths with maximum megapixel density.
- **HLS Video Pin Assembly**: For video pins, OVD reconstructs the HLS playlist chunks into standard MP4 files.
"""
    },
    {
        "title": "YouTube 4K & 1080p60 Video Extraction: Understanding Container Formats (MP4 vs WebM)",
        "platform": "YouTube",
        "category": "YouTube Guides",
        "readTime": "5 min read",
        "summary": "A deep dive into why YouTube streams high-resolution video and audio on separate tracks, and how ffmpeg merging delivers pristine universal files.",
        "image": "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?w=800&auto=format&fit=crop&q=80",
        "content": """### The Evolution of YouTube Adaptive Streaming (DASH)
Since 2020, YouTube does not serve 1080p, 1440p, or 4K videos as single monolithic files. Instead, it serves adaptive video streams (often using VP9 or AV1 codecs) completely separate from the audio stream (Opus/AAC).

### Why Merging is Essential:
- **Audio Synchronization**: Merging combines the highest bitrate video stream with the best audio track into a standard H.264 MP4 container.
- **Universal Compatibility**: MP4 container files work out-of-the-box on iPhone, Android, Windows, and macOS without additional codecs.
"""
    },
    {
        "title": "Facebook Video & Reel Downloader: How to Save Public Watch Content in 1080p",
        "platform": "Facebook",
        "category": "Facebook Guides",
        "readTime": "4 min read",
        "summary": "How to extract HD reels and long-form Facebook Watch broadcasts directly to your computer or phone without intrusive browser software.",
        "image": "https://images.unsplash.com/photo-1544717305-2782549b5136?w=800&auto=format&fit=crop&q=80",
        "content": """### Facebook's Video Architecture
Facebook serves video in both SD (Standard Definition) and HD (High Definition) progressive streams, as well as adaptive segmented streams for live broadcasts.

### How to Download in Full HD:
- Look for the 1080p or 720p stream indicator in OVD's format selector.
- Direct downloads bypass third-party browser plugins and intrusive pop-up networks.
"""
    },
    {
        "title": "How to Extract MP3 Audio from Social Media Clips (320kbps Lossless Quality)",
        "platform": "Universal",
        "category": "Audio Extraction",
        "readTime": "3 min read",
        "summary": "Convert trending sounds, podcast snippets, and background music from reels and shorts into clean MP3 audio files.",
        "image": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800&auto=format&fit=crop&q=80",
        "content": """### Audio Extraction Without Re-Encoding
Many online converters re-compress audio files, introducing digital hiss and clipping. OVD extracts the native audio stream directly from the video container.

### Highlights:
- **Bitrate Preservation**: Pulls original AAC/M4A/Opus streams up to 320 kbps.
- **Universal Tagging**: Generates standard MP3 format compatible with all car stereos, smart devices, and editing DAWs.
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
