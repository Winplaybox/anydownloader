"""
GravityClaw catalog: output TARGETS (which AI tool the prompt is for) and PRESETS
(ready-made forms so users understand what to type).

Every target carries a `syntax` guide that is injected into the LLM system prompt,
a `params` schema that the engine enforces itself (so parameter syntax is always valid),
and `checks` used by the local quality scorer.
"""

from __future__ import annotations

from typing import Any, Dict, List

CATEGORIES: List[Dict[str, str]] = [
    {"id": "image", "name": "Image", "icon": "image", "description": "Photos, art, thumbnails, product shots, characters"},
    {"id": "video", "name": "Video", "icon": "video", "description": "Text-to-video and image-to-video shots, ads, reels"},
    {"id": "text", "name": "Chat / LLM", "icon": "chat", "description": "System prompts and task prompts for ChatGPT, Claude, Gemini"},
    {"id": "agent", "name": "Code & App Agents", "icon": "code", "description": "Build prompts for Antigravity, Claude Code, Cursor, Lovable, Bolt, v0"},
    {"id": "music", "name": "Music & Audio", "icon": "music", "description": "Songs, bhajans, jingles, background scores, SFX"},
    {"id": "voice", "name": "Voice", "icon": "mic", "description": "TTS direction and voice-over scripts"},
    {"id": "content", "name": "Content & Marketing", "icon": "megaphone", "description": "Scripts, blogs, captions, ads, emails"},
    {"id": "design", "name": "Design", "icon": "palette", "description": "Logos, UI screens, posters, brand kits"},
]

_IMG_CHECKS = ["subject", "style", "lighting", "composition", "color", "detail"]
_VID_CHECKS = ["subject", "action", "camera", "shot", "lighting", "style", "duration"]
_LLM_CHECKS = ["role", "context", "task", "constraints", "format"]
_MUSIC_CHECKS = ["genre", "mood", "tempo", "instruments", "vocals"]

ASPECT_RATIOS = ["1:1", "16:9", "9:16", "4:5", "3:2", "2:3", "21:9"]

TARGETS: Dict[str, Dict[str, Any]] = {
    # ------------------------------------------------------------------ IMAGE
    "midjourney": {
        "name": "Midjourney v7", "category": "image", "tool_url": "https://www.midjourney.com/imagine",
        "length": [25, 80], "negative": "param",
        "syntax": (
            "Write ONE flowing comma-separated description: subject first, then medium/style, environment, "
            "lighting, camera/lens, color palette, mood, fine details. No sentences like 'create an image of'. "
            "Do NOT write any --parameters in the prompt text; put them in `parameters`. "
            "Put unwanted elements as a short comma list in `negative_prompt` (becomes --no)."
        ),
        "params": {"ar": {"type": "aspect", "default": "1:1"}, "stylize": {"type": "int", "min": 0, "max": 1000, "default": 250},
                   "chaos": {"type": "int", "min": 0, "max": 100, "default": 0}, "weird": {"type": "int", "min": 0, "max": 3000, "default": 0},
                   "v": {"type": "enum", "options": ["7", "6.1", "niji 6"], "default": "7"},
                   "quality": {"type": "enum", "options": ["1", "2", "4"], "default": "1"},
                   "raw": {"type": "bool", "default": False}},
        "checks": _IMG_CHECKS,
    },
    "flux": {
        "name": "FLUX.1 / FLUX Kontext", "category": "image", "tool_url": "https://playground.bfl.ai",
        "length": [40, 150], "negative": "none",
        "syntax": (
            "FLUX understands natural language. Write 2-5 vivid descriptive sentences in priority order: "
            "subject & action, setting, style/medium, lighting, camera & lens, color, mood. "
            "Put any text that must appear in the image in double quotes. FLUX ignores negative prompts: "
            "phrase exclusions positively (e.g. 'clean empty background')."
        ),
        "params": {"aspect_ratio": {"type": "aspect", "default": "1:1"}, "guidance": {"type": "float", "min": 1.5, "max": 5, "default": 3.5},
                   "steps": {"type": "int", "min": 4, "max": 50, "default": 28}, "seed": {"type": "seed"}},
        "checks": _IMG_CHECKS,
    },
    "sdxl_comfyui": {
        "name": "Stable Diffusion XL / ComfyUI", "category": "image", "tool_url": "https://github.com/comfyanonymous/ComfyUI",
        "length": [25, 75], "negative": "field",
        "syntax": (
            "Tag-style comma-separated tokens, most important first. Use emphasis weights like (keyword:1.2) "
            "sparingly (max 4, range 1.05-1.4). Include quality tokens (masterpiece, best quality, highly detailed) "
            "only once. ALWAYS provide a strong `negative_prompt` (artifacts, anatomy errors, watermark, text, blur, etc.)."
        ),
        "params": {"width": {"type": "int", "min": 512, "max": 2048, "default": 1024}, "height": {"type": "int", "min": 512, "max": 2048, "default": 1024},
                   "steps": {"type": "int", "min": 10, "max": 60, "default": 30}, "cfg": {"type": "float", "min": 1, "max": 15, "default": 6.5},
                   "sampler": {"type": "enum", "options": ["dpmpp_2m", "dpmpp_2m_sde", "euler_a", "euler", "dpmpp_3m_sde"], "default": "dpmpp_2m"},
                   "scheduler": {"type": "enum", "options": ["karras", "normal", "exponential", "sgm_uniform"], "default": "karras"},
                   "seed": {"type": "seed"}},
        "checks": _IMG_CHECKS + ["negative"],
    },
    "gpt_image": {
        "name": "ChatGPT Image (GPT-Image)", "category": "image", "tool_url": "https://chatgpt.com",
        "length": [50, 220], "negative": "none",
        "syntax": (
            "Write a clear, structured natural-language brief: purpose, subject, composition & layout, style, lighting, "
            "colors, exact text in quotes with font feel, and what to avoid in a final 'Avoid:' sentence. "
            "Great for infographics, posters and text-heavy images."
        ),
        "params": {"size": {"type": "enum", "options": ["1024x1024", "1536x1024", "1024x1536"], "default": "1024x1024"},
                   "quality": {"type": "enum", "options": ["low", "medium", "high"], "default": "high"}},
        "checks": _IMG_CHECKS,
    },
    "gemini_image": {
        "name": "Gemini Image (Nano Banana)", "category": "image", "tool_url": "https://gemini.google.com",
        "length": [40, 180], "negative": "none",
        "syntax": (
            "Describe the scene narratively (not keyword lists). For edits, state exactly what to change and what "
            "must stay identical (face, pose, background). Mention camera angle, lens, lighting and style explicitly."
        ),
        "params": {"aspect_ratio": {"type": "aspect", "default": "1:1"}},
        "checks": _IMG_CHECKS,
    },
    "ideogram": {
        "name": "Ideogram 3", "category": "image", "tool_url": "https://ideogram.ai",
        "length": [30, 150], "negative": "field",
        "syntax": "Best for typography. Put all visible text in double quotes, specify font style, placement and layout, then style and colors.",
        "params": {"aspect_ratio": {"type": "aspect", "default": "1:1"},
                   "style": {"type": "enum", "options": ["auto", "general", "realistic", "design", "3d", "anime"], "default": "auto"}},
        "checks": _IMG_CHECKS,
    },
    "leonardo": {
        "name": "Leonardo AI", "category": "image", "tool_url": "https://app.leonardo.ai",
        "length": [25, 100], "negative": "field",
        "syntax": "Descriptive comma-separated prompt with subject, style, lighting, lens, mood. Provide a negative prompt.",
        "params": {"aspect_ratio": {"type": "aspect", "default": "1:1"}, "alchemy": {"type": "bool", "default": True}},
        "checks": _IMG_CHECKS,
    },
    # ------------------------------------------------------------------ VIDEO
    "veo3": {
        "name": "Google Veo 3", "category": "video", "tool_url": "https://labs.google/fx/tools/flow",
        "length": [60, 220], "negative": "field",
        "syntax": (
            "Structure in this order as prose: Shot type & camera movement; Subject (appearance); Action; Setting; "
            "Lighting & time of day; Style/film look; Audio: ambient sound, SFX, music; Dialogue lines as "
            "Character says: \"...\" (keep lines short, max ~8s of speech). One continuous shot per prompt."
        ),
        "params": {"duration_s": {"type": "int", "min": 4, "max": 8, "default": 8}, "aspect_ratio": {"type": "enum", "options": ["16:9", "9:16"], "default": "16:9"},
                   "audio": {"type": "bool", "default": True}},
        "checks": _VID_CHECKS + ["audio"],
    },
    "sora": {
        "name": "OpenAI Sora 2", "category": "video", "tool_url": "https://sora.com",
        "length": [60, 220], "negative": "none",
        "syntax": "Cinematic prose: describe the shot like a director (camera, framing, lens), subject, motion beats in order, environment, lighting, mood, sound.",
        "params": {"duration_s": {"type": "int", "min": 4, "max": 20, "default": 10}, "aspect_ratio": {"type": "enum", "options": ["16:9", "9:16", "1:1"], "default": "16:9"}},
        "checks": _VID_CHECKS,
    },
    "kling": {
        "name": "Kling 2.x", "category": "video", "tool_url": "https://klingai.com",
        "length": [40, 160], "negative": "field",
        "syntax": "Formula: Subject + subject motion + scene + camera language + lighting + atmosphere. Use explicit camera verbs (dolly in, orbit, crane up, tracking). Provide negative prompt (blur, morphing, extra limbs).",
        "params": {"duration_s": {"type": "enum", "options": ["5", "10"], "default": "5"}, "aspect_ratio": {"type": "enum", "options": ["16:9", "9:16", "1:1"], "default": "9:16"},
                   "cfg_scale": {"type": "float", "min": 0, "max": 1, "default": 0.5}, "mode": {"type": "enum", "options": ["standard", "pro"], "default": "pro"}},
        "checks": _VID_CHECKS,
    },
    "runway": {
        "name": "Runway Gen-4", "category": "video", "tool_url": "https://app.runwayml.com",
        "length": [25, 120], "negative": "none",
        "syntax": "Image-to-video friendly: focus on MOTION, not appearance (the image defines look). Simple direct sentences: camera movement, subject action, environment motion. Avoid negatives.",
        "params": {"duration_s": {"type": "enum", "options": ["5", "10"], "default": "5"}, "ratio": {"type": "enum", "options": ["1280:720", "720:1280", "960:960"], "default": "1280:720"}},
        "checks": ["action", "camera", "shot", "subject"],
    },
    "hailuo": {
        "name": "Hailuo / MiniMax Video", "category": "video", "tool_url": "https://hailuoai.video",
        "length": [40, 160], "negative": "none",
        "syntax": "Describe subject, action and camera with bracket camera commands like [Push in], [Pan left], [Tracking shot], then lighting and style.",
        "params": {"duration_s": {"type": "enum", "options": ["6", "10"], "default": "6"}},
        "checks": _VID_CHECKS,
    },
    "wan_comfyui": {
        "name": "Wan 2.x (ComfyUI, local)", "category": "video", "tool_url": "https://github.com/comfyanonymous/ComfyUI",
        "length": [40, 140], "negative": "field",
        "syntax": "Detailed English prose: subject, action, scene, camera, lighting, style. Strong negative prompt (static, blurry, jitter, deformed, watermark, subtitles).",
        "params": {"frames": {"type": "int", "min": 33, "max": 121, "default": 81}, "fps": {"type": "int", "min": 8, "max": 30, "default": 16},
                   "steps": {"type": "int", "min": 10, "max": 50, "default": 30}, "cfg": {"type": "float", "min": 1, "max": 10, "default": 5}, "seed": {"type": "seed"}},
        "checks": _VID_CHECKS + ["negative"],
    },
    # ------------------------------------------------------------------ TEXT / LLM
    "llm_system": {
        "name": "System prompt (ChatGPT / Claude / Gemini)", "category": "text", "tool_url": "https://chatgpt.com",
        "length": [150, 900], "negative": "none",
        "syntax": (
            "Write a production system prompt using clearly labelled sections in Markdown: # Role, # Context, # Objective, "
            "# Instructions (numbered), # Constraints & guardrails, # Output format (exact schema/template), "
            "# Examples (1-2 short), # Edge cases. Use second person ('You are...'). No filler."
        ),
        "params": {},
        "checks": _LLM_CHECKS + ["examples"],
    },
    "llm_task": {
        "name": "Task prompt (one-shot request)", "category": "text", "tool_url": "https://claude.ai",
        "length": [60, 450], "negative": "none",
        "syntax": "Single message prompt: context, exact task, inputs in XML-style tags, constraints, desired output format and length. End with what to do if information is missing.",
        "params": {},
        "checks": _LLM_CHECKS,
    },
    "custom_gpt": {
        "name": "Custom GPT / Gem / Project instructions", "category": "text", "tool_url": "https://chatgpt.com/gpts/editor",
        "length": [200, 1000], "negative": "none",
        "syntax": "Instruction set for a reusable assistant: identity, audience, capabilities, step-by-step workflow, tone, refusal rules, formatting, conversation starters (4).",
        "params": {},
        "checks": _LLM_CHECKS,
    },
    # ------------------------------------------------------------------ AGENTS
    "coding_agent": {
        "name": "Coding agent (Antigravity / Claude Code / Cursor)", "category": "agent", "tool_url": "https://antigravity.google",
        "length": [250, 1400], "negative": "none",
        "syntax": (
            "Markdown build brief for an autonomous coding agent: # Goal, # Context & existing stack, # Requirements "
            "(functional, numbered), # Non-functional (security, performance, accessibility), # Architecture & file plan, "
            "# Step-by-step plan, # Acceptance criteria (testable checklist), # Constraints (do NOT ...), # Deliverables. "
            "Demand tests, no placeholder code, no fake data, and a final verification step."
        ),
        "params": {},
        "checks": ["role", "context", "task", "constraints", "format", "acceptance"],
    },
    "app_builder": {
        "name": "App builder (Lovable / Bolt / v0)", "category": "agent", "tool_url": "https://lovable.dev",
        "length": [150, 900], "negative": "none",
        "syntax": "Product spec style: one-line pitch, target users, pages/screens list with key components, data model, auth, integrations, visual style (colors, typography, vibe), responsive rules. Build in phases.",
        "params": {},
        "checks": ["context", "task", "format", "constraints"],
    },
    "n8n_workflow": {
        "name": "Workflow automation (n8n / Make / Zapier)", "category": "agent", "tool_url": "https://n8n.io",
        "length": [120, 700], "negative": "none",
        "syntax": "Describe trigger, each node in order with inputs/outputs, credentials needed, error handling/retries, schedule, and the final output. Numbered steps.",
        "params": {},
        "checks": ["task", "context", "format", "constraints"],
    },
    # ------------------------------------------------------------------ MUSIC
    "suno": {
        "name": "Suno v4.5 / v5", "category": "music", "tool_url": "https://suno.com/create",
        "length": [8, 60], "negative": "field",
        "syntax": (
            "`prompt` = the STYLE field only: comma-separated genre, sub-genre, mood, tempo/BPM, key instruments, vocal type, "
            "production, era (max ~180 characters, NO artist names). Put full lyrics in `lyrics` with section tags "
            "[Intro] [Verse 1] [Pre-Chorus] [Chorus] [Bridge] [Outro]; short singable lines; Hindi/Hinglish written in Latin script "
            "unless Devanagari requested. `negative_prompt` = styles to exclude."
        ),
        "params": {"instrumental": {"type": "bool", "default": False}, "duration_hint": {"type": "enum", "options": ["short", "full"], "default": "full"}},
        "checks": _MUSIC_CHECKS + ["lyrics"],
    },
    "udio": {
        "name": "Udio", "category": "music", "tool_url": "https://www.udio.com",
        "length": [8, 60], "negative": "none",
        "syntax": "Tags-style prompt of genre, mood, instruments, vocals, production; lyrics separately with [Verse]/[Chorus] tags.",
        "params": {}, "checks": _MUSIC_CHECKS,
    },
    "elevenlabs_sfx": {
        "name": "ElevenLabs Sound Effects", "category": "music", "tool_url": "https://elevenlabs.io/sound-effects",
        "length": [8, 50], "negative": "none",
        "syntax": "Concrete acoustic description: source, action, environment/reverb, distance, intensity, duration.",
        "params": {"duration_s": {"type": "float", "min": 0.5, "max": 22, "default": 5}},
        "checks": ["subject", "action", "duration"],
    },
    # ------------------------------------------------------------------ VOICE
    "voice_over": {
        "name": "Voice-over script + TTS direction", "category": "voice", "tool_url": "https://elevenlabs.io",
        "length": [60, 500], "negative": "none",
        "syntax": "Return the narration text ready for TTS with pacing marks (… for pauses), emphasis in CAPS sparingly, plus voice direction (gender, age, accent, energy, speed, emotion) in `structure`.",
        "params": {"voice_style": {"type": "enum", "options": ["calm", "energetic", "dramatic", "devotional", "horror", "news"], "default": "energetic"}},
        "checks": ["task", "format"],
    },
    # ------------------------------------------------------------------ CONTENT
    "short_video_script": {
        "name": "Reels / Shorts script", "category": "content", "tool_url": "https://studio.youtube.com",
        "length": [80, 260], "negative": "none",
        "syntax": "Script with timecodes: HOOK (0-3s, pattern interrupt), BUILD, PAYOFF, CTA. Each line: [time] VISUAL: ... | VO: ... | TEXT: ... Under 60s spoken.",
        "params": {"duration_s": {"type": "int", "min": 15, "max": 90, "default": 45}},
        "checks": ["hook", "format", "task"],
    },
    "youtube_long": {
        "name": "YouTube long-form script", "category": "content", "tool_url": "https://studio.youtube.com",
        "length": [400, 2000], "negative": "none",
        "syntax": "Title options (3), thumbnail text, cold-open hook, chapters with timestamps, B-roll notes, retention re-hooks every ~90s, CTA, description and tags.",
        "params": {"minutes": {"type": "int", "min": 3, "max": 30, "default": 8}},
        "checks": ["hook", "format", "task"],
    },
    "seo_blog": {
        "name": "SEO blog article brief", "category": "content", "tool_url": "https://blog.winplaybox.in",
        "length": [200, 900], "negative": "none",
        "syntax": "A prompt that will make an LLM write a ranking article: primary + secondary keywords, search intent, H1/H2/H3 outline, FAQ (schema-ready), internal link slots, E-E-A-T notes, meta title (<60) & description (<155), word count.",
        "params": {"words": {"type": "int", "min": 600, "max": 4000, "default": 1500}},
        "checks": ["task", "format", "constraints", "context"],
    },
    "social_caption": {
        "name": "Social captions + hashtags", "category": "content", "tool_url": "https://www.instagram.com",
        "length": [30, 250], "negative": "none",
        "syntax": "Platform-native caption with hook first line, value, CTA, emojis only if brand allows, 10-20 targeted hashtags (mix broad/niche/branded).",
        "params": {"platform": {"type": "enum", "options": ["instagram", "youtube", "facebook", "x", "linkedin", "pinterest"], "default": "instagram"}},
        "checks": ["hook", "task", "format"],
    },
    "ad_copy": {
        "name": "Ad copy (Meta / Google)", "category": "content", "tool_url": "https://adsmanager.facebook.com",
        "length": [60, 400], "negative": "none",
        "syntax": "Provide primary text variants, headlines (<40 chars), descriptions, CTA button, angle used (pain, desire, proof, urgency), and compliance notes.",
        "params": {},
        "checks": ["hook", "task", "format", "constraints"],
    },
    "email": {
        "name": "Email / cold outreach", "category": "content", "tool_url": "https://mail.google.com",
        "length": [60, 300], "negative": "none",
        "syntax": "Subject lines (3), preview text, body under 150 words, single clear CTA, P.S. line, personalization tokens like {{first_name}}.",
        "params": {},
        "checks": ["task", "format", "hook"],
    },
    # ------------------------------------------------------------------ DESIGN
    "logo": {
        "name": "Logo design", "category": "design", "tool_url": "https://ideogram.ai",
        "length": [25, 120], "negative": "field",
        "syntax": "Brand name in quotes, logo type (wordmark, lettermark, emblem, mascot, abstract), symbol idea, shape language, 2-3 colors (hex), flat vector, white background, scalable, no mockup.",
        "params": {"aspect_ratio": {"type": "aspect", "default": "1:1"}},
        "checks": ["subject", "style", "color"],
    },
    "ui_screen": {
        "name": "UI screen / landing page", "category": "design", "tool_url": "https://v0.dev",
        "length": [120, 700], "negative": "none",
        "syntax": "Screen purpose, layout sections top-to-bottom, components with states, content hierarchy, design tokens (colors, type scale, radius, spacing), responsive behavior, accessibility.",
        "params": {"platform": {"type": "enum", "options": ["web", "android", "ios", "desktop"], "default": "web"}},
        "checks": ["task", "format", "style", "constraints"],
    },
    "thumbnail": {
        "name": "YouTube thumbnail", "category": "design", "tool_url": "https://ideogram.ai",
        "length": [30, 120], "negative": "field",
        "syntax": "High-contrast 16:9 composition: one focal subject with exaggerated emotion, 2-4 word bold text in quotes, rule of thirds, saturated complementary colors, clean background, readable at small size.",
        "params": {"aspect_ratio": {"type": "aspect", "default": "16:9"}},
        "checks": _IMG_CHECKS,
    },
}

# Fields: key, label, type (text|textarea|select|number|chips), required, options, placeholder
PRESETS: List[Dict[str, Any]] = [
    {"id": "yt_short_viral", "name": "Viral YouTube Short script", "category": "content", "target": "short_video_script",
     "description": "Hook-first 30-60s Shorts/Reels script with visuals & on-screen text.",
     "fields": [{"key": "topic", "label": "Topic", "type": "text", "required": True, "placeholder": "Why trains in India have yellow lines"},
                {"key": "niche", "label": "Niche", "type": "select", "options": ["facts", "mythology", "horror", "food", "tech", "finance", "motivation", "kids story"]},
                {"key": "language", "label": "Language", "type": "select", "options": ["Hindi", "Hinglish", "English", "Marathi", "Tamil", "Telugu"]}],
     "template": "Write a viral {niche} short-video script about: {topic}. Spoken language: {language}."},
    {"id": "product_photo", "name": "E-commerce product photo", "category": "image", "target": "flux",
     "description": "Amazon/Flipkart-ready studio product shot.",
     "fields": [{"key": "product", "label": "Product", "type": "text", "required": True, "placeholder": "matte black steel water bottle"},
                {"key": "background", "label": "Background", "type": "select", "options": ["pure white", "lifestyle kitchen", "marble table", "gradient studio", "outdoor nature"]},
                {"key": "mood", "label": "Mood", "type": "text", "placeholder": "premium, minimal"}],
     "template": "Professional e-commerce product photograph of {product} on a {background} background, mood: {mood}."},
    {"id": "anime_character", "name": "Anime character sheet", "category": "image", "target": "midjourney",
     "description": "Consistent character design with turnaround.",
     "fields": [{"key": "character", "label": "Character", "type": "textarea", "required": True, "placeholder": "young Indian warrior girl with silver braid"},
                {"key": "style", "label": "Style", "type": "select", "options": ["Ghibli", "modern anime", "chibi", "manga ink", "cel-shaded"]}],
     "template": "Character design sheet, front/side/back turnaround and expressions of {character}, {style} style."},
    {"id": "devotional_art", "name": "Devotional deity artwork", "category": "image", "target": "gemini_image",
     "description": "Respectful, divine, highly detailed Sanatan Dharma art.",
     "fields": [{"key": "deity", "label": "Deity / scene", "type": "text", "required": True, "placeholder": "Lord Krishna playing flute at Vrindavan sunrise"},
                {"key": "style", "label": "Style", "type": "select", "options": ["cinematic 3D", "Raja Ravi Varma painting", "Tanjore gold leaf", "anime", "watercolor"]}],
     "template": "Respectful devotional artwork of {deity}, {style} style, divine glow, accurate traditional iconography."},
    {"id": "cinematic_ad_veo", "name": "Cinematic product ad (Veo 3)", "category": "video", "target": "veo3",
     "description": "8-second ad shot with sound design and a voice line.",
     "fields": [{"key": "product", "label": "Product / brand", "type": "text", "required": True},
                {"key": "setting", "label": "Setting", "type": "text", "placeholder": "rainy Mumbai street at night"},
                {"key": "line", "label": "Spoken tagline", "type": "text", "placeholder": "Taste the monsoon."}],
     "template": "8-second cinematic ad for {product} in {setting}. Voice line: '{line}'."},
    {"id": "horror_scene", "name": "Horror reel scene", "category": "video", "target": "kling",
     "description": "Found-footage Indian horror shot.",
     "fields": [{"key": "scene", "label": "Scene", "type": "textarea", "required": True, "placeholder": "abandoned haveli corridor, lantern flickers, shadow crosses"}],
     "template": "Found-footage horror video shot: {scene}. Slow dread, VHS look."},
    {"id": "train_reel", "name": "Train / railway reel shot", "category": "video", "target": "kling",
     "description": "Epic railway cinematography for train channels.",
     "fields": [{"key": "train", "label": "Train & location", "type": "text", "required": True, "placeholder": "Vande Bharat crossing Godavari bridge"},
                {"key": "time", "label": "Time / weather", "type": "select", "options": ["golden hour", "monsoon rain", "foggy dawn", "night lights", "snow"]}],
     "template": "Cinematic railway shot: {train} at {time}."},
    {"id": "system_prompt_bot", "name": "Customer support chatbot", "category": "text", "target": "llm_system",
     "description": "Production system prompt for a support assistant.",
     "fields": [{"key": "business", "label": "Business", "type": "text", "required": True},
                {"key": "policies", "label": "Key policies", "type": "textarea", "placeholder": "refund in 7 days, COD available"},
                {"key": "tone", "label": "Tone", "type": "select", "options": ["friendly", "formal", "Hinglish casual"]}],
     "template": "System prompt for a customer-support assistant of {business}. Policies: {policies}. Tone: {tone}."},
    {"id": "build_app_agent", "name": "Build a full app (coding agent)", "category": "agent", "target": "coding_agent",
     "description": "Enterprise build brief for Antigravity / Claude Code.",
     "fields": [{"key": "app", "label": "What to build", "type": "textarea", "required": True},
                {"key": "stack", "label": "Stack", "type": "text", "placeholder": "React + Vite, FastAPI, Supabase"},
                {"key": "must", "label": "Must-haves", "type": "textarea"}],
     "template": "Build: {app}. Stack: {stack}. Must-haves: {must}."},
    {"id": "landing_page", "name": "Landing page (Lovable / v0)", "category": "agent", "target": "app_builder",
     "description": "Conversion-focused landing page spec.",
     "fields": [{"key": "product", "label": "Product", "type": "text", "required": True}, {"key": "audience", "label": "Audience", "type": "text"},
                {"key": "vibe", "label": "Visual vibe", "type": "text", "placeholder": "dark, neon, glassmorphism"}],
     "template": "Landing page for {product} targeting {audience}. Visual vibe: {vibe}."},
    {"id": "automation_flow", "name": "Automation workflow (n8n)", "category": "agent", "target": "n8n_workflow",
     "description": "Describe a business process, get a node-by-node workflow brief.",
     "fields": [{"key": "process", "label": "Process", "type": "textarea", "required": True, "placeholder": "When a YouTube video is uploaded, post it to Insta, FB and X"}],
     "template": "Automation workflow for: {process}."},
    {"id": "bhajan_song", "name": "Devotional bhajan song", "category": "music", "target": "suno",
     "description": "Suno-ready bhajan with style + lyrics.",
     "fields": [{"key": "deity", "label": "Deity / theme", "type": "text", "required": True}, {"key": "language", "label": "Language", "type": "select", "options": ["Hindi", "Sanskrit", "Marathi", "Gujarati"]},
                {"key": "mood", "label": "Mood", "type": "select", "options": ["peaceful", "energetic kirtan", "emotional", "aarti"]}],
     "template": "Devotional {language} bhajan for {deity}, mood {mood}."},
    {"id": "brand_jingle", "name": "Brand jingle", "category": "music", "target": "suno",
     "description": "Catchy 30s jingle.",
     "fields": [{"key": "brand", "label": "Brand", "type": "text", "required": True}, {"key": "message", "label": "Message", "type": "text"}],
     "template": "30-second catchy jingle for {brand}. Message: {message}."},
    {"id": "bg_score", "name": "Background score (instrumental)", "category": "music", "target": "suno",
     "description": "Instrumental BGM for videos.",
     "fields": [{"key": "use", "label": "Use", "type": "text", "required": True, "placeholder": "horror story narration"}],
     "template": "Instrumental background score for {use}. No vocals."},
    {"id": "story_voiceover", "name": "Story narration voice-over", "category": "voice", "target": "voice_over",
     "description": "TTS-ready narration with voice direction.",
     "fields": [{"key": "story", "label": "Story / topic", "type": "textarea", "required": True}, {"key": "language", "label": "Language", "type": "select", "options": ["Hindi", "Hinglish", "English"]}],
     "template": "Voice-over narration in {language} for: {story}."},
    {"id": "seo_article", "name": "SEO article that ranks", "category": "content", "target": "seo_blog",
     "description": "Keyword-driven article brief.",
     "fields": [{"key": "keyword", "label": "Primary keyword", "type": "text", "required": True}, {"key": "audience", "label": "Audience", "type": "text"}],
     "template": "SEO article targeting '{keyword}' for {audience}."},
    {"id": "insta_caption", "name": "Instagram caption pack", "category": "content", "target": "social_caption",
     "description": "Captions + hashtags for a post.",
     "fields": [{"key": "post", "label": "Post about", "type": "text", "required": True}],
     "template": "Instagram caption for a post about {post}."},
    {"id": "meta_ad", "name": "Meta ad copy", "category": "content", "target": "ad_copy",
     "description": "High-converting ad variants.",
     "fields": [{"key": "offer", "label": "Offer", "type": "text", "required": True}, {"key": "audience", "label": "Audience", "type": "text"}],
     "template": "Meta ads for the offer: {offer}. Audience: {audience}."},
    {"id": "cold_email", "name": "Cold outreach email", "category": "content", "target": "email",
     "description": "Short personalised cold email.",
     "fields": [{"key": "offer", "label": "What you sell", "type": "text", "required": True}, {"key": "prospect", "label": "Prospect type", "type": "text"}],
     "template": "Cold email selling {offer} to {prospect}."},
    {"id": "yt_thumbnail", "name": "Click-worthy thumbnail", "category": "design", "target": "thumbnail",
     "description": "High-CTR thumbnail prompt.",
     "fields": [{"key": "video", "label": "Video title", "type": "text", "required": True}],
     "template": "YouTube thumbnail for the video: {video}."},
    {"id": "brand_logo", "name": "Brand logo", "category": "design", "target": "logo",
     "description": "Clean vector logo concept.",
     "fields": [{"key": "brand", "label": "Brand name", "type": "text", "required": True}, {"key": "industry", "label": "Industry", "type": "text"},
                {"key": "type", "label": "Logo type", "type": "select", "options": ["wordmark", "lettermark", "emblem", "mascot", "abstract"]}],
     "template": "{type} logo for '{brand}', industry: {industry}."},
    {"id": "app_screen", "name": "Mobile app screen", "category": "design", "target": "ui_screen",
     "description": "Detailed UI screen spec.",
     "fields": [{"key": "screen", "label": "Screen", "type": "text", "required": True, "placeholder": "Downloader home with paste link box"},
                {"key": "platform", "label": "Platform", "type": "select", "options": ["web", "android", "ios"]}],
     "template": "UI screen: {screen} for {platform}."},
    {"id": "enhance_prompt", "name": "Enhance my prompt", "category": "image", "target": "auto", "mode": "enhance",
     "description": "Paste any rough prompt - GravityClaw upgrades it for your chosen tool.",
     "fields": [{"key": "prompt", "label": "Your prompt", "type": "textarea", "required": True}],
     "template": "{prompt}"},
]

PRESETS_BY_ID = {p["id"]: p for p in PRESETS}

STYLE_PRESETS = [
    "cinematic photorealism", "Pixar 3D", "Studio Ghibli watercolor", "modern anime", "2D flat vector",
    "VHS analog horror", "Tanjore gold leaf", "cyberpunk neon", "minimal line art", "oil painting",
    "isometric 3D", "claymation", "comic book", "ultra-detailed macro", "documentary",
]
TONES = ["neutral", "professional", "friendly", "witty", "dramatic", "inspirational", "devotional", "suspenseful", "Hinglish casual"]
LANGUAGES = ["English", "Hindi", "Hinglish", "Marathi", "Gujarati", "Tamil", "Telugu", "Bengali", "Kannada", "Malayalam",
             "Punjabi", "Spanish", "Portuguese", "Indonesian", "Arabic", "French", "German", "Japanese"]


def public_catalog() -> Dict[str, Any]:
    targets = []
    for tid, t in TARGETS.items():
        targets.append({
            "id": tid, "name": t["name"], "category": t["category"], "tool_url": t["tool_url"],
            "supports_negative": t["negative"] != "none",
            "params": t["params"],
        })
    return {
        "version": "2.0.0",
        "categories": CATEGORIES,
        "targets": targets,
        "presets": PRESETS,
        "styles": STYLE_PRESETS,
        "tones": TONES,
        "languages": LANGUAGES,
        "aspect_ratios": ASPECT_RATIOS,
        "limits": {"requirement_max_chars": 4000, "variants_max": 5},
    }
