import re
import unicodedata
import urllib.parse
from typing import Optional

def summarize_title(title: Optional[str], max_words: int = 5, max_chars: int = 35) -> str:
    """
    Extracts a concise, clean, filesystem-safe summary slug from a media title.
    - Strips URLs and hashtags
    - Strips noisy bracketed tags like (Official Video), [4K], etc.
    - Strips emojis and illegal filename symbols
    - Prefers Latin words for highest filesystem compatibility when mixed
    - Preserves clean Unicode/Devanagari/international letters when pure non-Latin
    - Limits to max_words and max_chars without breaking words
    """
    if not title:
        return ""
    t = str(title).strip()
    # 1. Remove URLs
    t = re.sub(r'https?://\S+|www\.\S+', '', t)
    # 2. Remove hashtags
    t = re.sub(r'#\S+', '', t)
    # 3. Remove common bracketed video noise
    t = re.sub(r'\s*[\(\[\{][^\)\]\}]*(?:official|music|video|audio|lyrics?|hd|4k|1080p|remastered|visualizer|mv|shorts?|reels?)[^\)\]\}]*[\)\]\}]', '', t, flags=re.I)
    # 4. Remove emojis / high-surrogate pictographs
    t = re.sub(r'[\U00010000-\U0010ffff]', '', t)
    # 5. Replace separators and illegal symbols with spaces
    t = re.sub(r'[\/\\:*\?\"<>|•~`!@$%^&*()+=\[\]{};,.\-_]+', ' ', t)

    words = t.split()
    if not words:
        return ""

    latin_words = [re.sub(r'[^a-zA-Z0-9]', '', w) for w in words]
    latin_words = [w for w in latin_words if w]

    # If title has at least 2 clean Latin words or all words are Latin, use them for universal compatibility
    target_words = latin_words if (len(latin_words) >= 2 or (latin_words and len(words) <= 3)) else words

    clean_words = []
    curr_len = 0
    for w in target_words:
        # Keep letters (L), marks/accents/matras (M), numbers (N)
        w_clean = ''.join(c for c in w if unicodedata.category(c)[0] in ('L', 'M', 'N')).strip('_')
        if not w_clean:
            continue
        if len(clean_words) >= max_words or (curr_len + len(w_clean) + 1 > max_chars and clean_words):
            break
        clean_words.append(w_clean)
        curr_len += len(w_clean) + 1

    res = "_".join(clean_words).strip("_")
    res = re.sub(r'_+', '_', res)
    return res[:max_chars].rstrip('_')

def make_download_filename(title: Optional[str], platform: str, label: str, ext: str = "mp4") -> str:
    """
    Constructs a filename in the format:
    <short_summarized_title>-<platform>_<label>.<ext>
    e.g. Hanuman_Chalisa-youtube_320kbps_Audio_MP3.mp3
    """
    short_title = summarize_title(title)
    plat = re.sub(r'[^a-zA-Z0-9]', '', (platform or 'media').lower())
    lbl = re.sub(r'[^a-zA-Z0-9._-]', '_', label or 'download').strip('_')
    lbl = re.sub(r'_+', '_', lbl) or 'download'
    clean_ext = ext.lstrip('.').lower() or 'mp4'

    base = f"{plat}_{lbl}"
    if short_title:
        return f"{short_title}-{base}.{clean_ext}"
    return f"{base}.{clean_ext}"

def safe_content_disposition(filename: str, disposition_type: str = "attachment") -> str:
    """
    Constructs an RFC 5987 / RFC 6266 compliant Content-Disposition header.
    Provides an ASCII fallback for standard header parser safety (prevents latin-1 crash)
    and UTF-8 encoded filename* for modern browsers.
    """
    safe_fn = filename.replace('\r', '').replace('\n', '').replace('"', '').strip() or "download.mp4"
    ascii_clean = re.sub(r'[^a-zA-Z0-9._-]', '_', safe_fn)
    ascii_clean = re.sub(r'_+', '_', ascii_clean).strip('_-') or "download"
    if "." in safe_fn:
        ext = safe_fn.rsplit(".", 1)[-1]
        if not ascii_clean.endswith(f".{ext}"):
            ascii_clean = f"{ascii_clean}.{ext}"

    quoted_utf8 = urllib.parse.quote(safe_fn)
    return f'{disposition_type}; filename="{ascii_clean}"; filename*=UTF-8\'\'{quoted_utf8}'
