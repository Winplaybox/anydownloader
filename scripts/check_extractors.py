import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.utils.url_normalizer import normalize_url
from backend.extractors.registry import registry

SAMPLE_URLS = [
    ("Twitter/X Video", "https://x.com/NASA/status/1800000000"),
    ("Twitter/X Photo", "https://x.com/NASA/status/1800000001"),
    ("YouTube Video", "https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
    ("YouTube Shorts", "https://www.youtube.com/shorts/5qap5aO4i9A"),
    ("Instagram Reel", "https://www.instagram.com/reel/C1234567890/"),
    ("TikTok Video", "https://www.tiktok.com/@tiktok/video/7123456789012345678"),
    ("Facebook Video", "https://www.facebook.com/watch/?v=1234567890"),
]

async def check_all():
    print("=" * 60)
    print("OVD EXTRACTOR SUITE HEALTH CHECK")
    print("=" * 60)

    for label, sample in SAMPLE_URLS:
        try:
            norm = normalize_url(sample, resolve_redirects=False)
            extractor = registry.get(norm["platform"])
            if not extractor:
                print(f"[FAIL] {label}: No extractor registered for platform '{norm['platform']}'")
                continue

            matches = extractor.matches(norm["url"])
            if not matches:
                print(f"[FAIL] {label}: Extractor did not match URL {norm['url']}")
                continue

            print(f"[PASS] {label}: Normalized to {norm['url']} (platform: {norm['platform']}, extractor: {extractor.__class__.__name__})")
        except Exception as e:
            print(f"[WARN] {label}: {e}")

    print("=" * 60)
    print("Health check completed.")

if __name__ == "__main__":
    asyncio.run(check_all())
