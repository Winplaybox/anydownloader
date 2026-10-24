from typing import Dict, Optional

try:
    from backend.extractors.base import BaseExtractor
    from backend.extractors.twitter import TwitterExtractor
    from backend.extractors.instagram import InstagramExtractor
    from backend.extractors.tiktok import TikTokExtractor
    from backend.extractors.facebook import FacebookExtractor
    from backend.extractors.youtube import YouTubeExtractor
    from backend.extractors.pinterest import PinterestExtractor
    from backend.extractors.reddit import RedditExtractor
    from backend.extractors.generic import GenericExtractor
except ModuleNotFoundError:
    from extractors.base import BaseExtractor
    from extractors.twitter import TwitterExtractor
    from extractors.instagram import InstagramExtractor
    from extractors.tiktok import TikTokExtractor
    from extractors.facebook import FacebookExtractor
    from extractors.youtube import YouTubeExtractor
    from extractors.pinterest import PinterestExtractor
    from extractors.reddit import RedditExtractor
    from extractors.generic import GenericExtractor

class ExtractorRegistry:
    def __init__(self):
        self._extractors: Dict[str, BaseExtractor] = {}
        # Core Social Media Extractors
        self.register(TwitterExtractor())
        self.register(InstagramExtractor())
        self.register(TikTokExtractor())
        self.register(FacebookExtractor())
        self.register(YouTubeExtractor())
        self.register(PinterestExtractor())
        self.register(RedditExtractor())
        # Generic Website & Fallback Extractor
        self._generic = GenericExtractor()

    def register(self, extractor: BaseExtractor):
        self._extractors[extractor.platform] = extractor

    def get(self, platform: str) -> Optional[BaseExtractor]:
        if platform == "generic":
            return self._generic
        return self._extractors.get(platform)

    def find_for_url(self, url: str) -> Optional[BaseExtractor]:
        for ext in self._extractors.values():
            if ext.matches(url):
                return ext
        return self._generic

registry = ExtractorRegistry()
