from typing import Dict, Optional
from backend.extractors.base import BaseExtractor
from backend.extractors.twitter import TwitterExtractor
from backend.extractors.instagram import InstagramExtractor
from backend.extractors.tiktok import TikTokExtractor
from backend.extractors.facebook import FacebookExtractor
from backend.extractors.youtube import YouTubeExtractor

class ExtractorRegistry:
    def __init__(self):
        self._extractors: Dict[str, BaseExtractor] = {}
        # Register Phase 1 extractors
        self.register(TwitterExtractor())
        self.register(InstagramExtractor())
        self.register(TikTokExtractor())
        self.register(FacebookExtractor())
        self.register(YouTubeExtractor())

    def register(self, extractor: BaseExtractor):
        self._extractors[extractor.platform] = extractor

    def get(self, platform: str) -> Optional[BaseExtractor]:
        return self._extractors.get(platform)

    def find_for_url(self, url: str) -> Optional[BaseExtractor]:
        for ext in self._extractors.values():
            if ext.matches(url):
                return ext
        return None

registry = ExtractorRegistry()
