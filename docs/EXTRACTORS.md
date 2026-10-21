# OVD Extractor Architecture & Developer Guide

This document describes how media extraction works in OVD, how to add support for new platforms (e.g., Pinterest, Reddit), and how to debug and repair extractors when upstream platform APIs change.

---

## 1. Architecture Overview

Extraction follows a strict pipeline:

```
Client Input → normalizeUrl() → detectPlatform() → POST /api/resolve
   → Extractor[platform].resolve(url) → ResolveResult
   → UI Result Card → GET /api/download?token=... (Signed HMAC Proxy) → Browser Download
```

### Key Principles:
1. **Isolated Responsibilities**: Each platform has its own dedicated extractor file (`backend/extractors/<platform>.py`) implementing `BaseExtractor`.
2. **Unified Data Schema**: All extractors return `ResolveResult`, consisting of `MediaItem`s and `MediaVariant`s.
3. **No Direct Upstream URLs in Client**: Downloader URLs are cryptographically signed HMAC tokens (`/api/download?token=...`) with 5-minute TTL.
4. **SSRF Guard**: The download proxy verifies that the upstream media CDN host is in the safe allowlist (`video.twimg.com`, `pbs.twimg.com`, `googlevideo.com`, `fbcdn.net`, `cdninstagram.com`, `tiktokcdn.com`, etc.) and resolves DNS to block private, loopback, and intranet IPs (RFC 1918 / link-local).
5. **No Raw Errors Leaked**: Extractors raise typed `AppError(ErrorCode.XYZ)` with friendly user-facing messages.

---

## 2. Core Interfaces & Types

### 2.1 Extractor Interface (`backend/extractors/base.py`)
```python
class BaseExtractor(ABC):
    platform: str

    @abstractmethod
    def matches(self, url: str) -> bool:
        """Determines if the extractor can handle the given normalized URL."""
        pass

    @abstractmethod
    async def resolve(self, url: str) -> ResolveResult:
        """Resolves the URL into media items and variants."""
        pass
```

### 2.2 Result Schema
```python
@dataclass
class MediaVariant:
    id: str
    kind: "video" | "image"
    ext: str                 # "mp4", "jpg", "png", "webp", "gif"
    url: str                 # Upstream CDN URL (hidden from client)
    quality: Optional[str]   # "1080p", "720p", "orig", "large", "GIF"
    width: Optional[int]
    height: Optional[int]
    hasAudio: Optional[bool]
    downloadUrl: Optional[str] # Signed proxy token /api/download?token=...

@dataclass
class MediaItem:
    index: int
    kind: "video" | "image"
    variants: List[MediaVariant]
    thumbnail: Optional[str]
    durationSec: Optional[float]

@dataclass
class ResolveResult:
    platform: str
    sourceUrl: str
    items: List[MediaItem]
    title: Optional[str]
    author: Optional[AuthorInfo]
```

---

## 3. How to Add a New Platform Extractor

To add a platform in Phase 2 (e.g., Pinterest or Reddit):

### Step 1: Create `backend/extractors/<platform>.py`
Create a new file inheriting from `BaseExtractor`:
```python
from backend.extractors.base import BaseExtractor, ResolveResult, MediaItem, MediaVariant
from backend.utils.errors import AppError, ErrorCode

class PinterestExtractor(BaseExtractor):
    platform: str = "pinterest"

    def matches(self, url: str) -> bool:
        return "pinterest.com" in url or "pin.it" in url

    async def resolve(self, url: str) -> ResolveResult:
        # Implement fallback chain: primary API -> secondary fallback
        ...
```

### Step 2: Register in `backend/extractors/registry.py`
Import and register the new extractor in `ExtractorRegistry.__init__`:
```python
from backend.extractors.pinterest import PinterestExtractor

self.register(PinterestExtractor())
```

### Step 3: Add URL Patterns to Normalizers
- In `backend/utils/url_normalizer.py`: add host detection and tracking param stripping.
- In `src/utils/normalizeUrl.js`: add client-side matching.

### Step 4: Add Upstream CDN to Security Allowlist
If the platform uses a new media CDN (e.g., `i.pinimg.com`, `v.redd.it`), add the domain pattern to `ALLOWED_CDN_DOMAINS` in `backend/utils/security.py`.

### Step 5: Add Health Check & Unit Tests
- Add a sample URL to `SAMPLE_URLS` in `scripts/check_extractors.py`.
- Create unit test `tests/test_<platform>.py`.

---

## 4. How to Debug a Broken Extractor

When a social media platform changes its frontend or API:

### 1. Run the Extractor Health Check
```bash
npm run check:extractors
```
This tests URL normalization and matching across all platforms.

### 2. Run the Automated Test Suite
```bash
python -m unittest discover tests
```
Inspect failing tests to identify if the issue is schema mismatch, missing variants, or network timeouts.

### 3. Verify the Upstream Fallback Chain
Each extractor uses a multi-tier fallback:
- **Twitter/X**: Tier 1 = FxTwitter API (`api.fxtwitter.com/i/status/{id}`), Tier 2 = `yt-dlp`.
- **Instagram**: Tier 1 = Polaris GraphQL JSON in page shell, Tier 2 = `yt-dlp`.
- **TikTok**: Tier 1 = TikWM API (watermark-free MP4 + photo slides), Tier 2 = `yt-dlp`.
- **Facebook**: Tier 1 = `yt-dlp`, Tier 2 = OpenGraph & regex extraction.
- **YouTube**: Tier 1 = `yt-dlp` progressive MP4 streams + maxres thumbnail generation.

If Tier 1 fails, verify whether the API endpoint changed its payload format or requires updated user-agent headers.

### 4. Logging & Privacy Rules
- Log error code, platform name, and execution duration only.
- **Never log full URLs containing personal tracking parameters or query tokens.**
- Never log raw API response dumps in production.
