"""Static catalogs for the AI Video Editor: languages, voices, caption styles, modes.

Everything the UI shows comes from here (GET /api/editor/options), so adding a
language, voice or caption style is a one-line change.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# --------------------------------------------------------------------------- #
# Languages
#   kokoro: Kokoro lang code (None = Kokoro can't speak it, Edge voices only)
#   font:   ASS font family used for captions written in the native script
#   indic:  native script is non-Latin and a Roman (Hinglish-style) option makes sense
# --------------------------------------------------------------------------- #
LANGUAGES: List[Dict[str, Any]] = [
    {"id": "hi", "name": "Hindi / Hinglish", "kokoro": "hi", "font": "Noto Sans Devanagari Black", "indic": True},
    {"id": "en-in", "name": "English (India)", "kokoro": "en-gb", "font": "Inter Black", "indic": False},
    {"id": "en-us", "name": "English (US)", "kokoro": "en-us", "font": "Inter Black", "indic": False},
    {"id": "en-gb", "name": "English (UK)", "kokoro": "en-gb", "font": "Inter Black", "indic": False},
    {"id": "mr", "name": "Marathi", "kokoro": None, "font": "Noto Sans Devanagari Black", "indic": True},
    {"id": "gu", "name": "Gujarati", "kokoro": None, "font": "Noto Sans Gujarati Black", "indic": True},
    {"id": "bn", "name": "Bengali", "kokoro": None, "font": "Noto Sans Bengali Black", "indic": True},
    {"id": "ta", "name": "Tamil", "kokoro": None, "font": "Noto Sans Tamil Black", "indic": True},
    {"id": "te", "name": "Telugu", "kokoro": None, "font": "Noto Sans Telugu Black", "indic": True},
    {"id": "kn", "name": "Kannada", "kokoro": None, "font": "Noto Sans Kannada Black", "indic": True},
    {"id": "ml", "name": "Malayalam", "kokoro": None, "font": "Noto Sans Malayalam Black", "indic": True},
    {"id": "pa", "name": "Punjabi", "kokoro": None, "font": "Noto Sans Gurmukhi Black", "indic": True},
    {"id": "ur", "name": "Urdu", "kokoro": None, "font": "Noto Sans Arabic Black", "indic": True},
    {"id": "ar", "name": "Arabic", "kokoro": None, "font": "Noto Sans Arabic Black", "indic": False},
    {"id": "es", "name": "Spanish", "kokoro": "es", "font": "Inter Black", "indic": False},
    {"id": "fr", "name": "French", "kokoro": "fr-fr", "font": "Inter Black", "indic": False},
    {"id": "it", "name": "Italian", "kokoro": "it", "font": "Inter Black", "indic": False},
    {"id": "pt", "name": "Portuguese (BR)", "kokoro": "pt-br", "font": "Inter Black", "indic": False},
    {"id": "de", "name": "German", "kokoro": None, "font": "Inter Black", "indic": False},
    {"id": "ru", "name": "Russian", "kokoro": None, "font": "Inter Black", "indic": False},
    {"id": "id", "name": "Indonesian", "kokoro": None, "font": "Inter Black", "indic": False},
]
LANG_BY_ID = {l["id"]: l for l in LANGUAGES}

# --------------------------------------------------------------------------- #
# Voices. engine=kokoro runs locally (free, offline after first model download);
# engine=edge uses Microsoft Edge online voices (free, needs network).
# --------------------------------------------------------------------------- #
_K = "kokoro"
_E = "edge"
VOICES: List[Dict[str, Any]] = [
    # Hindi
    {"id": "hm_omega", "engine": _K, "lang": "hi", "name": "Omega", "gender": "Male", "desc": "Kokoro · deep news narrator"},
    {"id": "hm_psi", "engine": _K, "lang": "hi", "name": "Psi", "gender": "Male", "desc": "Kokoro · calm storyteller"},
    {"id": "hf_alpha", "engine": _K, "lang": "hi", "name": "Alpha", "gender": "Female", "desc": "Kokoro · clear & warm"},
    {"id": "hf_beta", "engine": _K, "lang": "hi", "name": "Beta", "gender": "Female", "desc": "Kokoro · soft & friendly"},
    {"id": "hi-IN-MadhurNeural", "engine": _E, "lang": "hi", "name": "Madhur", "gender": "Male", "desc": "Edge · energetic"},
    {"id": "hi-IN-SwaraNeural", "engine": _E, "lang": "hi", "name": "Swara", "gender": "Female", "desc": "Edge · smooth"},
    # English
    {"id": "am_michael", "engine": _K, "lang": "en-us", "name": "Michael", "gender": "Male", "desc": "Kokoro · confident narrator"},
    {"id": "am_fenrir", "engine": _K, "lang": "en-us", "name": "Fenrir", "gender": "Male", "desc": "Kokoro · deep & dramatic"},
    {"id": "am_puck", "engine": _K, "lang": "en-us", "name": "Puck", "gender": "Male", "desc": "Kokoro · upbeat"},
    {"id": "af_heart", "engine": _K, "lang": "en-us", "name": "Heart", "gender": "Female", "desc": "Kokoro · best quality, warm"},
    {"id": "af_bella", "engine": _K, "lang": "en-us", "name": "Bella", "gender": "Female", "desc": "Kokoro · energetic"},
    {"id": "af_nicole", "engine": _K, "lang": "en-us", "name": "Nicole", "gender": "Female", "desc": "Kokoro · whisper/ASMR"},
    {"id": "bm_george", "engine": _K, "lang": "en-gb", "name": "George", "gender": "Male", "desc": "Kokoro · British documentary"},
    {"id": "bm_fable", "engine": _K, "lang": "en-gb", "name": "Fable", "gender": "Male", "desc": "Kokoro · British storyteller"},
    {"id": "bf_emma", "engine": _K, "lang": "en-gb", "name": "Emma", "gender": "Female", "desc": "Kokoro · British clear"},
    {"id": "en-IN-PrabhatNeural", "engine": _E, "lang": "en-in", "name": "Prabhat", "gender": "Male", "desc": "Edge · Indian English"},
    {"id": "en-IN-NeerjaNeural", "engine": _E, "lang": "en-in", "name": "Neerja", "gender": "Female", "desc": "Edge · Indian English"},
    # Other Kokoro languages
    {"id": "em_alex", "engine": _K, "lang": "es", "name": "Alex", "gender": "Male", "desc": "Kokoro"},
    {"id": "ef_dora", "engine": _K, "lang": "es", "name": "Dora", "gender": "Female", "desc": "Kokoro"},
    {"id": "ff_siwis", "engine": _K, "lang": "fr", "name": "Siwis", "gender": "Female", "desc": "Kokoro"},
    {"id": "im_nicola", "engine": _K, "lang": "it", "name": "Nicola", "gender": "Male", "desc": "Kokoro"},
    {"id": "if_sara", "engine": _K, "lang": "it", "name": "Sara", "gender": "Female", "desc": "Kokoro"},
    {"id": "pm_alex", "engine": _K, "lang": "pt", "name": "Alex", "gender": "Male", "desc": "Kokoro"},
    {"id": "pf_dora", "engine": _K, "lang": "pt", "name": "Dora", "gender": "Female", "desc": "Kokoro"},
    # Edge-only languages
    {"id": "mr-IN-ManoharNeural", "engine": _E, "lang": "mr", "name": "Manohar", "gender": "Male", "desc": "Edge"},
    {"id": "mr-IN-AarohiNeural", "engine": _E, "lang": "mr", "name": "Aarohi", "gender": "Female", "desc": "Edge"},
    {"id": "gu-IN-NiranjanNeural", "engine": _E, "lang": "gu", "name": "Niranjan", "gender": "Male", "desc": "Edge"},
    {"id": "gu-IN-DhwaniNeural", "engine": _E, "lang": "gu", "name": "Dhwani", "gender": "Female", "desc": "Edge"},
    {"id": "bn-IN-BashkarNeural", "engine": _E, "lang": "bn", "name": "Bashkar", "gender": "Male", "desc": "Edge"},
    {"id": "bn-IN-TanishaaNeural", "engine": _E, "lang": "bn", "name": "Tanishaa", "gender": "Female", "desc": "Edge"},
    {"id": "ta-IN-ValluvarNeural", "engine": _E, "lang": "ta", "name": "Valluvar", "gender": "Male", "desc": "Edge"},
    {"id": "ta-IN-PallaviNeural", "engine": _E, "lang": "ta", "name": "Pallavi", "gender": "Female", "desc": "Edge"},
    {"id": "te-IN-MohanNeural", "engine": _E, "lang": "te", "name": "Mohan", "gender": "Male", "desc": "Edge"},
    {"id": "te-IN-ShrutiNeural", "engine": _E, "lang": "te", "name": "Shruti", "gender": "Female", "desc": "Edge"},
    {"id": "kn-IN-GaganNeural", "engine": _E, "lang": "kn", "name": "Gagan", "gender": "Male", "desc": "Edge"},
    {"id": "kn-IN-SapnaNeural", "engine": _E, "lang": "kn", "name": "Sapna", "gender": "Female", "desc": "Edge"},
    {"id": "ml-IN-MidhunNeural", "engine": _E, "lang": "ml", "name": "Midhun", "gender": "Male", "desc": "Edge"},
    {"id": "ml-IN-SobhanaNeural", "engine": _E, "lang": "ml", "name": "Sobhana", "gender": "Female", "desc": "Edge"},
    {"id": "pa-IN-OjasNeural", "engine": _E, "lang": "pa", "name": "Ojas", "gender": "Male", "desc": "Edge"},
    {"id": "pa-IN-VaaniNeural", "engine": _E, "lang": "pa", "name": "Vaani", "gender": "Female", "desc": "Edge"},
    {"id": "ur-IN-SalmanNeural", "engine": _E, "lang": "ur", "name": "Salman", "gender": "Male", "desc": "Edge"},
    {"id": "ur-IN-GulNeural", "engine": _E, "lang": "ur", "name": "Gul", "gender": "Female", "desc": "Edge"},
    {"id": "ar-SA-HamedNeural", "engine": _E, "lang": "ar", "name": "Hamed", "gender": "Male", "desc": "Edge"},
    {"id": "ar-SA-ZariyahNeural", "engine": _E, "lang": "ar", "name": "Zariyah", "gender": "Female", "desc": "Edge"},
    {"id": "de-DE-ConradNeural", "engine": _E, "lang": "de", "name": "Conrad", "gender": "Male", "desc": "Edge"},
    {"id": "de-DE-KatjaNeural", "engine": _E, "lang": "de", "name": "Katja", "gender": "Female", "desc": "Edge"},
    {"id": "ru-RU-DmitryNeural", "engine": _E, "lang": "ru", "name": "Dmitry", "gender": "Male", "desc": "Edge"},
    {"id": "ru-RU-SvetlanaNeural", "engine": _E, "lang": "ru", "name": "Svetlana", "gender": "Female", "desc": "Edge"},
    {"id": "id-ID-ArdiNeural", "engine": _E, "lang": "id", "name": "Ardi", "gender": "Male", "desc": "Edge"},
    {"id": "id-ID-GadisNeural", "engine": _E, "lang": "id", "name": "Gadis", "gender": "Female", "desc": "Edge"},
]
VOICE_BY_ID = {v["id"]: v for v in VOICES}
# en-in may use any English voice; Kokoro voice lang is checked against this family map.
_LANG_FAMILY = {"en-in": {"en-in", "en-us", "en-gb"}, "en-us": {"en-us", "en-gb", "en-in"}, "en-gb": {"en-gb", "en-us", "en-in"}}


def voices_for(lang: str) -> List[Dict[str, Any]]:
    fam = _LANG_FAMILY.get(lang, {lang})
    out = [v for v in VOICES if v["lang"] in fam]
    # exact language first, Kokoro before Edge
    return sorted(out, key=lambda v: (v["lang"] != lang, v["engine"] != _K))


def default_voice(lang: str) -> Optional[str]:
    vs = voices_for(lang)
    return vs[0]["id"] if vs else None


def voice_ok_for(voice_id: str, lang: str) -> bool:
    return any(v["id"] == voice_id for v in voices_for(lang))


# --------------------------------------------------------------------------- #
# Caption styles (rendered by captions.py). `preview` drives the CSS mock in the UI.
# --------------------------------------------------------------------------- #
CAPTION_STYLES: List[Dict[str, Any]] = [
    {"id": "pop", "name": "Pop Highlight", "desc": "3 words, bold white, spoken word pops in yellow (YouTube Create style)",
     "preview": {"text": "#FFFFFF", "active": "#FFE500", "outline": "#000000", "box": None}},
    {"id": "single", "name": "One Word Punch", "desc": "One big word at a time with a zoom pop. Fast, energetic",
     "preview": {"text": "#FFFFFF", "active": "#4DFF88", "outline": "#000000", "box": None}},
    {"id": "box", "name": "Boxed Phrase", "desc": "Phrase on a dark box, spoken word in accent color. Clean news look",
     "preview": {"text": "#FFFFFF", "active": "#FF4D4D", "outline": None, "box": "#000000"}},
    {"id": "karaoke", "name": "Karaoke Fill", "desc": "Words fill with color as they are spoken",
     "preview": {"text": "#FFFFFF", "active": "#00E5FF", "outline": "#000000", "box": None}},
    {"id": "minimal", "name": "Minimal Subtitle", "desc": "Full sentence, 2 lines, soft shadow. Calm & premium",
     "preview": {"text": "#FFFFFF", "active": "#FFFFFF", "outline": None, "box": None}},
    {"id": "none", "name": "No Captions", "desc": "Only voiceover, no burned-in text",
     "preview": None},
]
STYLE_IDS = {s["id"] for s in CAPTION_STYLES}

VOICEOVER_MODES: List[Dict[str, str]] = [
    {"id": "ai_mix", "name": "AI voiceover + original sound (low)", "desc": "Narration on top, real ambience kept quietly underneath"},
    {"id": "ai_replace", "name": "AI voiceover only", "desc": "Original audio muted"},
    {"id": "original", "name": "Keep original speech", "desc": "No voiceover, captions made from what is said in the video"},
]
MODE_IDS = {m["id"] for m in VOICEOVER_MODES}

CAPTION_SCRIPTS = [
    {"id": "roman", "name": "Roman (Hinglish style)", "desc": "e.g. 'Raat ko road par haadsa'"},
    {"id": "native", "name": "Native script", "desc": "e.g. 'रात को रोड पर हादसा'"},
]

OUTPUT_FORMATS = [
    {"id": "vertical", "name": "Vertical 9:16 (Shorts / Reels)"},
    {"id": "original", "name": "Keep original shape"},
]

ACCENT_PRESETS = ["#FFE500", "#4DFF88", "#00E5FF", "#FF4D4D", "#FF8A00", "#C77DFF", "#FFFFFF"]


def public_options() -> Dict[str, Any]:
    return {
        "languages": [{"id": l["id"], "name": l["name"], "indic": l["indic"]} for l in LANGUAGES],
        "voices": VOICES,
        "caption_styles": CAPTION_STYLES,
        "caption_scripts": CAPTION_SCRIPTS,
        "voiceover_modes": VOICEOVER_MODES,
        "output_formats": OUTPUT_FORMATS,
        "accent_presets": ACCENT_PRESETS,
    }
