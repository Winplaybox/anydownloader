"""
Spectra / Winplaybox Dynamic Art Direction & Visual Registry.
Provides 12+ extensible style presets with canonical visual specifications,
line quality, color palettes, proportions, shading, lighting, and rendering tokens.
"""

from typing import Dict, Any, Optional

ART_STYLES: Dict[str, Dict[str, Any]] = {
    "2d_flat_vector": {
        "id": "2d_flat_vector",
        "name": "2D Flat Vector Minimalist",
        "route_engine": "2D_ANIMATION_RIGS",
        "description": "Kurzgesagt-inspired clean geometric shapes, solid color fills, and warm pastel palette.",
        "line_quality": "Clean vector strokes with uniform line weights, no sketchy lines",
        "color_palette": {
            "background": "#FBF3EA (Warm Pastel Beige)",
            "primary": "#0D9488 (Teal) and #1E293B (Navy)",
            "accent": "#F97316 (Vibrant Orange)",
            "shadow": "Flat 10% opacity geometric drop shadow"
        },
        "character_proportions": "Simplified geometric proportions, rounded heads, minimalist features",
        "shading_style": "Zero gradients, zero photorealism, strictly flat 2D color blocks",
        "texture": "Smooth digital vector canvas, no grit or noise",
        "lighting_convention": "Ambient even studio illumination without directional glare",
        "background_detail": "Minimalist architectural shapes, high negative space",
        "depth_style": "Isometric or 2D orthographic layering",
        "camera_conventions": "Smooth horizontal pans, subtle dolly push-ins, centered framing",
        "animation_principles": "Puppet joint articulation, kinetic popups, clean easing",
        "positive_tokens": "minimalist 2D flat vector illustration, clean lines, corporate flat design, Kurzgesagt aesthetic, pastel beige background, solid flat color fills, simple geometric human character, cute minimal facial features, soft ambient shadows, no 3D rendering, no gradients, vector art style, high quality, 9:16 vertical",
        "negative_tokens": "3D render, photorealistic, realistic human skin, shiny, glossy, gradients, detailed textures, anime, noisy background, cinematic lighting, sketch, ugly, deformed limbs",
        "motion_style": "2D vector animation, smooth puppet joints, looping cycles, kinetic text popups, flat motion graphic"
    },
    "2d_cartoon": {
        "id": "2d_cartoon",
        "name": "2D Cartoon Classic",
        "route_engine": "2D_ANIMATION_RIGS",
        "description": "Classic Saturday-morning animation with dynamic line art, cel shading, and energetic expressions.",
        "line_quality": "Expressive ink outlines with tapered dynamic weights",
        "color_palette": {
            "background": "#F1F5F9 (Soft Slate)",
            "primary": "#2563EB (Royal Blue)",
            "accent": "#EF4444 (Crimson Red)",
            "shadow": "Crisp hard-edged cel shading"
        },
        "character_proportions": "Dynamic cartoon anatomy, large expressive hands and eyes",
        "shading_style": "2-tone cel shading with distinct highlight cuts",
        "texture": "Clean animation cel with subtle paper tooth",
        "lighting_convention": "Bright theatrical key lighting with crisp cast shadows",
        "background_detail": "Hand-inked animated background plates",
        "depth_style": "Multi-plane cel depth with blurred foreground elements",
        "camera_conventions": "Fast whip pans, dynamic zooms, dutch angles during action",
        "animation_principles": "Classic squash and stretch, anticipation, exaggerated motion arcs",
        "positive_tokens": "classic 2D cartoon animation, cel shaded, bold inking outlines, dynamic expressive cartoon character, vibrant primary colors, Saturday morning animation aesthetic, clean 9:16 portrait",
        "negative_tokens": "photorealistic, 3D CGI, plastic, desaturated, grainy, dull, rough unfinished sketch",
        "motion_style": "Energetic cartoon squash and stretch, fluid character arcs, expressive eye blinks"
    },
    "3d_pixar": {
        "id": "3d_pixar",
        "name": "3D Pixar & Disney Animation",
        "route_engine": "COMFYUI_VIDEO_DIT",
        "description": "Rich subsurface scattering textures, expressive glass eyes, and warm studio rim lighting.",
        "line_quality": "Edge-free volumetric 3D surfaces with soft silhouettes",
        "color_palette": {
            "background": "#0F172A (Deep Ambient Studio)",
            "primary": "#38BDF8 (Cyan) and #F59E0B (Amber)",
            "accent": "#EC4899 (Pink Glow)",
            "shadow": "Soft contact ambient occlusion"
        },
        "character_proportions": "Stylized 3D appeal, slightly oversized head, emotive facial topology",
        "shading_style": "Subsurface scattering (SSS) skin, clay softness, micro-fiber cloth",
        "texture": "Tactile fabric weaves, soft hair grooming, glassy iris reflections",
        "lighting_convention": "Three-point Hollywood studio lighting with golden rim illumination",
        "background_detail": "Depth-of-field blurred volumetric 3D environment",
        "depth_style": "Shallow focus with bokeh and cinematic perspective",
        "camera_conventions": "Fluid Steadicam moves, crane sweeps, gentle tracking",
        "animation_principles": "Realistic physical weight, secondary cloth motion, micro-expressions",
        "positive_tokens": "Cute 3D Pixar Disney style character, big expressive glass eyes, smooth clay animation, Disney Pixar 8k lighting, subsurface scattering, warm volumetric rim light, rich color palette, cinematic render, portrait 9:16",
        "negative_tokens": "flat 2D vector, anime, harsh outlines, photorealistic human skin, gloomy, noisy, low poly, distorted face",
        "motion_style": "Fluid 3D character animation, expressive eye darts, squash and stretch, camera orbit, cinematic depth"
    },
    "3d_scientific_medical": {
        "id": "3d_scientific_medical",
        "name": "3D Medical & Engineering Cutaways",
        "route_engine": "COMFYUI_VIDEO_DIT",
        "description": "Semi-transparent frosted glass anatomical organs, glowing fluid dynamics, and biological cross-sections.",
        "line_quality": "Precision CAD technical edges with glowing laser accents",
        "color_palette": {
            "background": "#020617 (Dark Obsidian Lab)",
            "primary": "#06B6D4 (Bio-luminescent Cyan)",
            "accent": "#10B981 (Active Green) and #F43F5E (Oxygenated Red)",
            "shadow": "Clean translucent transmission with volumetric shadows"
        },
        "character_proportions": "Accurate human anatomical silhouette or isolated organ systems",
        "shading_style": "Frosted glass refraction, glowing internal bioluminescence",
        "texture": "Porous biological membranes, microscopic fluid droplets",
        "lighting_convention": "Dark medical studio with internal fiber-optic backlighting",
        "background_detail": "Dark blurred clinical laboratory or abstract particle void",
        "depth_style": "Extreme macroscopic focus with micro-particle depth",
        "camera_conventions": "Slow axial push-in, 360-degree anatomical orbit, microscopic zoom",
        "animation_principles": "Rhythmic vascular pulsation, laminar fluid flow, molecular binding",
        "positive_tokens": "3D medical animation, anatomical cutaway diagram, translucent frosted glass human anatomy, glowing internal fluid simulation, scientific volumetric particles, octane render, 8k ultra clarity, cinematic medical studio",
        "negative_tokens": "flat cartoon, anime, drawing, rough sketch, low resolution, messy colors, ugly anatomy, scary, bloody",
        "motion_style": "3D camera push-in, volumetric particle flow, expanding cross-section, slow-motion fluid dynamics"
    },
    "minimalist": {
        "id": "minimalist",
        "name": "Ultra Minimalist Line Art",
        "route_engine": "2D_ANIMATION_RIGS",
        "description": "High negative space, ultra-refined single stroke contours, and high-impact iconic silhouettes.",
        "line_quality": "Delicate single-pixel vector hairline with precision anchor points",
        "color_palette": {
            "background": "#FFFFFF (Pure White) or #FAFAFA",
            "primary": "#18181B (Charcoal Black)",
            "accent": "#2563EB (Singular Cobalt Accent)",
            "shadow": "Zero drop shadow, pure negative space"
        },
        "character_proportions": "Abstracted gesture silhouettes, poetic simplification",
        "shading_style": "Strictly unshaded negative space design",
        "texture": "Clean digital vector or smooth archival paper",
        "lighting_convention": "Theoretical flat illumination",
        "background_detail": "Empty negative space with subtle single-line architectural hints",
        "depth_style": "Strictly flat graphic design plane",
        "camera_conventions": "Static graphic lockup, subtle linear slide",
        "animation_principles": "Self-drawing strokes, morphing silhouettes, kinetic text transitions",
        "positive_tokens": "ultra minimalist line art, single continuous line drawing, elegant minimal human silhouette, high negative space, monochrome with single cobalt blue accent, modern museum aesthetic, pristine clean, 9:16",
        "negative_tokens": "cluttered, detailed, 3D, shading, textures, busy background, gradients, realistic, noisy",
        "motion_style": "Smooth line drawing animation, minimalist morphing vector silhouettes, elegant stroke reveal"
    },
    "anime_ghibli": {
        "id": "anime_ghibli",
        "name": "Anime & Studio Ghibli Watercolor",
        "route_engine": "COMFYUI_VIDEO_DIT",
        "description": "Hand-painted cel animation, watercolor skies, lush botanical nature, and soft atmospheric wind.",
        "line_quality": "Delicate pencil-traced cel outlines in warm sepia tone",
        "color_palette": {
            "background": "#E0F2FE (Soft Summer Sky)",
            "primary": "#15803D (Lush Meadow Green)",
            "accent": "#EA580C (Warm Terracotta)",
            "shadow": "Soft painterly wash in purple-blue tones"
        },
        "character_proportions": "Classic anime proportions, expressive emotional eyes, natural hair flow",
        "shading_style": "Hand-painted watercolor wash with paper tooth bleed",
        "texture": "Cold-press watercolor paper grain, gouache brush strokes",
        "lighting_convention": "Golden afternoon sunlight filtering through dappled tree canopies",
        "background_detail": "Rich botanical backgrounds, clouds painted with impressionist brushwork",
        "depth_style": "Atmospheric haze with natural multi-plane depth",
        "camera_conventions": "Slow contemplative pans, gentle upward tilts into expansive skies",
        "animation_principles": "Wind rustling through clothes and foliage, natural breathing cycles",
        "positive_tokens": "Studio Ghibli style, hand-drawn anime cel animation, lush watercolor background, vibrant painted nature, soft morning sunlight, Makoto Shinkai aesthetic, wind blowing through trees, painterly masterpiece",
        "negative_tokens": "3D CGI, plastic, photorealistic, harsh CGI, ugly sketch, modern vector flat, noisy, dark gritty",
        "motion_style": "Gentle anime wind rustling, hair swaying, hand-drawn cinematic panning, soft particle dust"
    },
    "storybook": {
        "id": "storybook",
        "name": "Children's Storybook Illustration",
        "route_engine": "2D_ANIMATION_RIGS",
        "description": "Warm textured gouache, cozy storybook appeal, whimsical proportions, and gentle contours.",
        "line_quality": "Soft colored pencil contour with textured edges",
        "color_palette": {
            "background": "#FEF3C7 (Warm Butter Cream)",
            "primary": "#D97706 (Amber) and #047857 (Forest Green)",
            "accent": "#DC2626 (Berry Red)",
            "shadow": "Textured stipple or gouache dry-brush shading"
        },
        "character_proportions": "Whimsical rounded shapes, friendly proportions, warm rosy cheeks",
        "shading_style": "Dry brush gouache blending with tactile paper feel",
        "texture": "Heavy linen book paper, colored pencil grain",
        "lighting_convention": "Cozy bedtime warm lamp glow, soft storybook daylight",
        "background_detail": "Charming illustrated cottages, playful whimsical nature",
        "depth_style": "Layered paper collage depth, gentle focal blur",
        "camera_conventions": "Storybook page-turn wipes, gentle rocking camera, slow zoom",
        "animation_principles": "Gentle puppet bobbing, cozy micro-gestures, twinkle effects",
        "positive_tokens": "childrens storybook illustration, textured gouache painting, colored pencil details, cozy warm colors, whimsical cute character, storybook bedtime aesthetic, charming and comforting, 9:16",
        "negative_tokens": "photorealistic, 3D CGI, gritty, horror, dark, neon, futuristic, harsh digital outlines",
        "motion_style": "Gentle storybook puppet movement, soft drifting sparkles, comforting character nods"
    },
    "cinematic_realism": {
        "id": "cinematic_realism",
        "name": "Cinematic 4K Photorealism",
        "route_engine": "COMFYUI_VIDEO_DIT",
        "description": "35mm anamorphic photography, shallow depth of field, natural lighting, and authentic textures.",
        "line_quality": "Zero artificial outlines; pure photographic contrast and optical sharpness",
        "color_palette": {
            "background": "#1E293B (Cinematic Slate)",
            "primary": "#334155 (Subdued Tones)",
            "accent": "#F59E0B (Natural Sunlight or Practical Lamp)",
            "shadow": "Natural photographic shadow roll-off with deep blacks"
        },
        "character_proportions": "Realistic anatomical human proportions and posture",
        "shading_style": "Physically based rendering (PBR), natural skin subsurface scattering",
        "texture": "Natural skin pores, cloth fibers, environmental dust motes",
        "lighting_convention": "Natural window light, practical cinematic tungsten sources, soft bounce",
        "background_detail": "Authentic real-world interior or urban environment with optical bokeh",
        "depth_style": "Shallow depth of field (f/1.8 lens), beautiful circular bokeh",
        "camera_conventions": "Smooth handheld gimbal tracking, rack focus, gentle Steadicam slide",
        "animation_principles": "Natural human biomechanics, realistic eye saccades, breathing",
        "positive_tokens": "Hyper-realistic cinematic 8K, shot on 35mm Arri Alexa, anamorphic lens flare, shallow depth of field, photorealistic textures, volumetric lighting, Octane render, photoreal masterpiece, 9:16",
        "negative_tokens": "cartoon, 2D vector, anime, painting, CGI plastic look, fake, blur, low quality, oversaturated",
        "motion_style": "Smooth Steadicam glide, slow tracking dolly, rack focus, natural human micro-movements"
    },
    "clay_animation": {
        "id": "clay_animation",
        "name": "Claymation & Stop Motion",
        "route_engine": "COMFYUI_VIDEO_DIT",
        "description": "Tactile plasticine clay modeling, subtle thumbprint textures, and physical stop-motion lighting.",
        "line_quality": "Physical sculpted clay edges with organic soft bevels",
        "color_palette": {
            "background": "#F5F5F4 (Warm Studio Plaster)",
            "primary": "#EA580C (Terracotta Clay) and #0284C7 (Blue Clay)",
            "accent": "#84CC16 (Lime Green Clay)",
            "shadow": "Real tabletop studio softbox shadows"
        },
        "character_proportions": "Chunky clay modeling, tactile ball-and-socket armature appeal",
        "shading_style": "Real miniature physical lighting on plasticine clay",
        "texture": "Microscopic thumbprints, clay seams, malleable soft surface",
        "lighting_convention": "Tabletop miniature studio lighting with softboxes and reflectors",
        "background_detail": "Cardboard and sculpted foam miniature dioramas",
        "depth_style": "Macro tilt-shift depth of field, miniature tabletop focus",
        "camera_conventions": "Stop-motion incremental camera moves, slightly stepped frame cadence",
        "animation_principles": "Stepped 12fps stop-motion timing, physical clay deformation",
        "positive_tokens": "claymation style, plasticine clay characters, Aardman stop motion aesthetic, visible fingerprint clay texture, tactile miniature studio lighting, handmade clay set, 9:16",
        "negative_tokens": "2D vector, digital flat, smooth plastic, photorealistic human, noisy digital render",
        "motion_style": "Tactile 12fps stop motion animation, subtle clay surface deformation, physical puppet steps"
    },
    "paper_cutout": {
        "id": "paper_cutout",
        "name": "Paper Cutout & Layered Collage",
        "route_engine": "2D_ANIMATION_RIGS",
        "description": "Multi-layered cardstock, cast drop shadows between sheets, craft paper texture, and stop-motion charm.",
        "line_quality": "Slightly irregular hand-cut paper scissor edges",
        "color_palette": {
            "background": "#F3F4F6 (Textured Paper White)",
            "primary": "#4F46E5 (Indigo Cardstock)",
            "accent": "#F59E0B (Mustard Cardstock)",
            "shadow": "Authentic physical drop shadows between layered paper sheets"
        },
        "character_proportions": "Segmented paper cutout limbs joined by brass paper brads",
        "shading_style": "Zero digital shading; depth created entirely by paper layer shadows",
        "texture": "Heavy watercolor paper, fibrous cardstock, subtle kraft paper grain",
        "lighting_convention": "Overhead desk lamp creating distinct cast shadows under each paper layer",
        "background_detail": "Stacked geometric paper layers creating stylized scenery",
        "depth_style": "Layered multi-plane physical shadow depth",
        "camera_conventions": "Top-down down-shooter camera or slight perspective angle",
        "animation_principles": "Hinged cutout limb rotation, sliding paper layers, playful pops",
        "positive_tokens": "paper cutout animation style, layered craft paper collage, cast paper shadows, textured cardstock, handmade South Park / cutout aesthetic, crisp paper edges, 9:16",
        "negative_tokens": "3D photorealism, glossy plastic, smooth vector, airbrush, lens flare, motion blur",
        "motion_style": "Charming paper cutout puppet movement, hinged limb rotation, sliding paper layers"
    },
    "watercolor": {
        "id": "watercolor",
        "name": "Fluid Watercolor & Ink",
        "route_engine": "2D_ANIMATION_RIGS",
        "description": "Wet-on-wet pigment blooms, bleeding watercolor edges, rough cotton rag paper, and artistic splatters.",
        "line_quality": "Loose sumi-e ink washes and expressive broken lines",
        "color_palette": {
            "background": "#F8FAFC (Rough Arches Paper)",
            "primary": "#0284C7 (Cobalt Blue Wash)",
            "accent": "#E11D48 (Carmine Red Splash)",
            "shadow": "Translucent burnt umber wash"
        },
        "character_proportions": "Impressionistic fluid human gestures, artistic suggestion over rigid anatomy",
        "shading_style": "Wet-on-wet pigment bleeding, edge blooms, drying rings",
        "texture": "Heavy 300gsm cold-press cotton watercolor paper with visible deckled tooth",
        "lighting_convention": "Natural gallery daylight illuminating pigment luminosity",
        "background_detail": "Abstract washes of atmospheric tone, impressionist vignettes",
        "depth_style": "Atmospheric pigment dissipation",
        "camera_conventions": "Slow fluid drifts, gentle macro focus pulls across wet paint",
        "animation_principles": "Pigment dissolving and blooming across paper, flowing brush strokes",
        "positive_tokens": "fluid watercolor painting, wet on wet paint blooms, rough cold press paper texture, loose expressive ink contours, transparent washes of color, artistic masterpiece, 9:16",
        "negative_tokens": "3D CGI, vector flat, plastic, photorealistic, harsh neon, cluttered, digital solid fills",
        "motion_style": "Fluid watercolor pigment bloom animation, drifting wash transitions, organic color bleed"
    },
    "pixel_art": {
        "id": "pixel_art",
        "name": "Retro 16-Bit Pixel Art",
        "route_engine": "2D_ANIMATION_RIGS",
        "description": "Crisp integer-scaled pixel grid, limited retro color palette, and nostalgic 16-bit RPG charm.",
        "line_quality": "Strict 1-pixel raster outlines without anti-aliasing blur",
        "color_palette": {
            "background": "#1E1B4B (Midnight Indigo)",
            "primary": "#38BDF8 (Vibrant Cyan)",
            "accent": "#FACC15 (Golden Coin Yellow)",
            "shadow": "Strict dithered shading (checkerboard pixel patterns)"
        },
        "character_proportions": "Classic 16-bit sprite proportions (chibi or detailed isometric)",
        "shading_style": "Hand-placed pixel clusters, limited 16-color ramp per sprite",
        "texture": "Crisp integer nearest-neighbor pixels, zero bilinear blur",
        "lighting_convention": "High-contrast arcade game lighting, glowing 8-bit lamps",
        "background_detail": "Tile-based scenic parallax backgrounds",
        "depth_style": "Multiple layered 2D parallax scrolling planes",
        "camera_conventions": "Smooth horizontal tile scrolling, locked pixel grid tracking",
        "animation_principles": "Frame-by-frame 8-frame walk cycles, pixel-art particle bursts",
        "positive_tokens": "16-bit pixel art, detailed retro video game sprite, crisp pixel grid, vibrant nostalgic palette, isometric pixel aesthetic, Chrono Trigger / Octopath style, 9:16",
        "negative_tokens": "blurry, anti-aliased, 3D, photorealistic, smooth vector, modern CGI, high poly",
        "motion_style": "Authentic 16-bit pixel frame animation, smooth multi-plane parallax scroll, 8-frame walk loop"
    },
    "custom": {
        "id": "custom",
        "name": "Custom User Art Direction",
        "route_engine": "COMFYUI_VIDEO_DIT",
        "description": "User-configured art style adapted to target video diffusion or animation rigs.",
        "line_quality": "Harmonized to user brief specifications",
        "color_palette": {
            "background": "Adaptive background tone",
            "primary": "Adaptive primary theme",
            "accent": "Adaptive accent tone",
            "shadow": "Natural contact shadows"
        },
        "character_proportions": "Balanced stylized proportions",
        "shading_style": "Clean contemporary digital rendering",
        "texture": "Balanced digital medium",
        "lighting_convention": "Balanced studio illumination",
        "background_detail": "Contextual narrative background",
        "depth_style": "Natural composition depth",
        "camera_conventions": "Story-driven cinematic framing",
        "animation_principles": "Physically grounded secondary motion",
        "positive_tokens": "high quality aesthetic illustration, clean composition, artistic styling, 9:16 portrait",
        "negative_tokens": "ugly, low quality, distorted, deformed, noisy, grainy",
        "motion_style": "Smooth cinematic motion, natural camera tracking"
    }
}


def get_art_style(style_key: Optional[str]) -> Dict[str, Any]:
    """
    Retrieves and normalizes an art style specification from the registry.
    Handles legacy aliases and falls back gracefully to 2d_flat_vector.
    """
    if not style_key:
        return ART_STYLES["2d_flat_vector"]

    key = str(style_key).strip().lower().replace(" ", "_").replace("-", "_")

    alias_map = {
        "vector": "2d_flat_vector",
        "flat_vector": "2d_flat_vector",
        "2d": "2d_flat_vector",
        "cartoon": "2d_cartoon",
        "pixar": "3d_pixar",
        "3d": "3d_pixar",
        "medical": "3d_scientific_medical",
        "scientific": "3d_scientific_medical",
        "anatomy": "3d_scientific_medical",
        "ghibli": "anime_ghibli",
        "anime": "anime_ghibli",
        "realistic": "cinematic_realism",
        "photoreal": "cinematic_realism",
        "realism": "cinematic_realism",
        "clay": "clay_animation",
        "claymation": "clay_animation",
        "paper": "paper_cutout",
        "cutout": "paper_cutout",
        "pixel": "pixel_art",
        "16bit": "pixel_art",
        "line_art": "minimalist",
        "minimal": "minimalist"
    }

    if key in ART_STYLES:
        return ART_STYLES[key]
    if key in alias_map and alias_map[key] in ART_STYLES:
        return ART_STYLES[alias_map[key]]

    return ART_STYLES["2d_flat_vector"]
