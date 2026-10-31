"""Choices shown in the Video Studio. Keep keys in sync with autopilot/styles.py in the AI Video Editor repo
(the worker turns them into picture prompts, caption looks and render settings)."""

STYLES = {
    "flat": "2D Explainer",
    "realistic": "Realistic", "3d-animation": "3D Animation", "anime": "Anime", "cinematic": "Cinematic",
    "vintage": "Vintage", "noir": "Noir", "digital-art": "Digital Art", "comic": "Comic Book", "pencil": "Pencil Sketch",
    "oil-painting": "Oil Painting", "watercolor": "Watercolor", "pop-art": "Pop Art", "impressionist": "Impressionist",
    "fantasy": "Fantasy", "dark-gothic": "Dark Gothic", "cyberpunk": "Cyberpunk", "surreal": "Surreal",
    "minimal": "Minimalistic", "pixel": "Pixel Art", "science-explainer": "Science Explainer", "low-poly": "Low Poly",
    "claymation": "Claymation", "storybook": "Storybook", "isometric": "Isometric", "paper-cutout": "Paper Cutout",
    "dramatic-3d": "Dramatic 3D", "neon-outline": "Neon Outline", "retro-anime": "Retro Anime",
    "glassmorphism": "Glassmorphism", "painted-anime": "Painted Anime", "ukiyo-e": "Ukiyo-e", "steampunk": "Steampunk",
    "vaporwave": "Vaporwave",
}

# Each caption look and the font its preview (and the rendered video) uses.
CAPTIONS = {
    "cinematic": {"label": "Cinematic", "font": "Playfair Display", "weight": 700},
    "koe": {"label": "Koe", "font": "EB Garamond", "weight": 500},
    "pill": {"label": "Pill", "font": "Lexend", "weight": 600},
    "hormozi": {"label": "Hormozi", "font": "Montserrat", "weight": 900},
    "beast": {"label": "Beast", "font": "Bangers", "weight": 400},
    "wrap": {"label": "Wrap", "font": "Lexend", "weight": 700},
    "noah": {"label": "Noah", "font": "Oswald", "weight": 700},
    "handwritten": {"label": "Handwritten", "font": "Caveat", "weight": 700},
    "subtitle": {"label": "Subtitle", "font": "DM Sans", "weight": 500},
    "impact": {"label": "Impact", "font": "Anton", "weight": 400},
    "pop": {"label": "Pop", "font": "Fredoka", "weight": 700},
    "chronicle": {"label": "Chronicle", "font": "Cinzel", "weight": 700},
    "cyber": {"label": "Cyber", "font": "Orbitron", "weight": 700},
    "grit": {"label": "Grit", "font": "Permanent Marker", "weight": 400},
    "luxe": {"label": "Luxe", "font": "Playfair Display", "weight": 700},
    "terminal": {"label": "Terminal", "font": "Space Mono", "weight": 700},
    "tiktok": {"label": "TikTok", "font": "TikTok Sans", "weight": 500},
    "none": {"label": "No captions", "font": None, "weight": None},
}

ASPECTS = {"9:16": "Tall (9:16)", "16:9": "Wide (16:9)", "1:1": "Square (1:1)"}
QUALITIES = {"basic": "Basic", "good": "Good", "premium": "Premium", "max": "Max"}
FREQUENCIES = {1: "Every day", 2: "Every 2 days", 3: "Every 3 days", 7: "Every week"}
MOODS = ["upbeat", "calm", "inspiring", "dramatic", "mysterious", "happy", "dark", "epic", "lofi"]

NICHES = {
    "health": "Health & everyday science", "finance": "Personal finance", "facts": "Mind-blowing facts",
    "motivation": "Motivation & self-improvement", "history": "History stories", "horror": "Scary stories",
    "tech": "Tech & AI explained", "kids": "Kids stories with a moral", "mythology": "Mythology stories",
    "psychology": "Psychology facts", "business": "Business stories", "travel": "Travel & places",
}

# Preset characters ("Elements"): the same look is reused in every scene so the person stays recognisable.
CHARACTERS = {
    "aria": "Aria", "sofia": "Sofia", "nadia": "Nadia", "lilly": "Lilly", "jess": "Jess", "chris": "Chris",
    "tyler": "Tyler", "sana": "Sana", "zara": "Zara", "rohan": "Rohan", "jake": "Jake", "yuki": "Yuki",
    "fatima": "Fatima", "darius": "Darius", "catherine": "Catherine", "valentina": "Valentina", "kevin": "Kevin",
    "aisha": "Aisha", "marcus": "Marcus", "ygritte": "Ygritte", "laura": "Laura", "brittany": "Brittany",
    "diana": "Diana", "emilia": "Emilia", "sierra": "Sierra", "hazel": "Hazel", "emma": "Emma", "ashley": "Ashley",
}

CATALOG = {
    "styles": STYLES, "captions": CAPTIONS, "aspects": ASPECTS, "qualities": QUALITIES,
    "frequencies": {str(k): v for k, v in FREQUENCIES.items()}, "moods": MOODS, "niches": NICHES,
    "characters": CHARACTERS, "caption_positions": ["top", "middle", "bottom"],
    "platforms": ["youtube", "tiktok", "instagram", "facebook", "threads", "x"],
}
