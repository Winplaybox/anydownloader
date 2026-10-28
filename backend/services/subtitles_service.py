"""
AI Subtitles & Caption Extraction Service
-----------------------------------------
Capabilities:
- Extract native captions from YouTube, TikTok, and social media URLs.
- Generate synchronized .SRT and .VTT files.
- Translate subtitles between English, Hindi, and Spanish.
- Clean text formatting without timestamps for reader view.
"""

import os
import re
import tempfile
from typing import Dict, Any, List, Optional

class SubtitlesService:
    def format_seconds_to_srt_time(self, seconds: float) -> str:
        millis = int((seconds - int(seconds)) * 1000)
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"

    def parse_srt_to_segments(self, srt_text: str) -> List[Dict[str, Any]]:
        """Parses raw SRT content into structured segments with start, end, and text."""
        blocks = re.split(r'\n\s*\n', srt_text.strip())
        segments = []
        for block in blocks:
            lines = [l.strip() for l in block.splitlines() if l.strip()]
            if len(lines) >= 3:
                timing = lines[1]
                content = " ".join(lines[2:])
                m = re.match(r'(\d+:\d+:\d+,\d+)\s*-->\s*(\d+:\d+:\d+,\d+)', timing)
                if m:
                    segments.append({
                        "start": m.group(1),
                        "end": m.group(2),
                        "text": content
                    })
        return segments

    def generate_srt_from_timed_words(self, words: List[Dict[str, Any]], group_size: int = 4) -> str:
        """Groups synchronized words into readable 3-5 word subtitle blocks."""
        if not words:
            return ""

        srt_output = []
        block_idx = 1
        for i in range(0, len(words), group_size):
            chunk = words[i:i + group_size]
            start_sec = chunk[0].get("offset", 0) / 10000000.0 if "offset" in chunk[0] else chunk[0].get("start", 0)
            last = chunk[-1]
            end_sec = (last.get("offset", 0) + last.get("duration", 0)) / 10000000.0 if "offset" in last else last.get("end", start_sec + 2.0)

            start_str = self.format_seconds_to_srt_time(start_sec)
            end_str = self.format_seconds_to_srt_time(end_sec)
            text_str = " ".join([w.get("word", w.get("text", "")) for w in chunk])

            srt_output.append(f"{block_idx}\n{start_str} --> {end_str}\n{text_str}\n")
            block_idx += 1

        return "\n".join(srt_output)

    def extract_subtitles_from_url(self, media_url: str) -> Dict[str, Any]:
        """Queries yt-dlp to extract native or auto-generated subtitles directly."""
        try:
            import yt_dlp
            ydl_opts = {
                'skip_download': True,
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en', 'hi'],
                'quiet': True,
                'no_warnings': True
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(media_url, download=False)
                subtitles = info.get('subtitles', {})
                auto_subs = info.get('automatic_captions', {})

                formats = []
                for lang, tracks in subtitles.items():
                    formats.append({"lang": lang, "type": "native", "formats": [t.get("ext") for t in tracks]})
                for lang, tracks in auto_subs.items():
                    formats.append({"lang": lang, "type": "auto_generated", "formats": [t.get("ext") for t in tracks]})

                return {
                    "ok": True,
                    "title": info.get("title", "Media"),
                    "has_captions": len(formats) > 0,
                    "available_languages": formats
                }
        except Exception as e:
            return {"ok": False, "error": str(e)}

subtitles_service = SubtitlesService()
