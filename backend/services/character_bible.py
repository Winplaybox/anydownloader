"""
Winplaybox / GravityClaw Persistent Character Bible & Environment Registry.
Manages canonical visual designs, reference assets, character consistency tracking,
and ensures characters are never forced into non-character shots (diagrams, infographics, landscapes).
"""

from typing import Dict, Any, List, Optional


class CharacterBibleManager:
    """
    Manages persistent character profiles and canonical design bibles.
    """

    def __init__(self):
        self._character_registry: Dict[str, Dict[str, Any]] = {}

    def resolve_character(
        self,
        topic_or_script: str,
        style_key: str = "2d_flat_vector",
        custom_char_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes or retrieves a persistent canonical character record matching the narrative domain.
        """
        lower = topic_or_script.lower()

        if custom_char_id and custom_char_id in self._character_registry:
            return self._character_registry[custom_char_id]

        if any(w in lower for w in ["gym", "workout", "muscle", "run", "fitness", "athlete", "exercise"]):
            char_id = "char_arjun_fitness_001"
            name = "Arjun"
            archetype = "Fitness & Wellness Practitioner"
            hair = "short neatly cropped black hair"
            face = "determined friendly geometric face, athletic jawline"
            top = "vibrant orange athletic performance tee"
            trousers = "navy training shorts with compression liner"
            shoes = "white minimalist training shoes"
            palette = ["#F97316 (Orange)", "#1E293B (Navy)", "#FFFFFF", "#10B981"]
            features = "subtle sweat highlight, relaxed active posture"
        elif any(w in lower for w in ["student", "study", "exam", "college", "book", "desk", "teen"]):
            char_id = "char_aarav_student_002"
            name = "Aarav"
            archetype = "Curious Young Scholar"
            hair = "slightly tousled dark hair with clean taper"
            face = "expressive wide eyes, round tortoise-shell spectacles"
            top = "mustard yellow casual hoodie over white collar"
            trousers = "dark indigo slim denim"
            shoes = "classic canvas sneakers"
            palette = ["#F59E0B (Mustard)", "#1E1B4B (Indigo)", "#FFFFFF", "#64748B"]
            features = "round glasses, inquisitive head-tilt gesture"
        elif any(w in lower for w in ["cheetah", "lion", "animal", "chico", "forest", "jungle", "wildlife"]):
            char_id = "char_chico_cheetah_003"
            name = "Chico"
            archetype = "Playful Animal Protagonist"
            hair = "golden sleek fur with distinctive geometric black rosettes"
            face = "large curious expressive eyes, cute rounded snout"
            top = "natural golden pelt with iconic black tear stripes"
            trousers = "athletic swift limbs with white paw tips"
            shoes = "bare padded paws"
            palette = ["#F59E0B (Golden Fur)", "#0F172A (Black Spots)", "#FEF3C7 (Cream)"]
            features = "long counter-balancing tail, bouncy dynamic gait"
        else:
            # Default relatable modern protagonist (Rohan)
            char_id = "char_rohan_explainer_001"
            name = "Rohan"
            archetype = "Relatable Modern Professional"
            hair = "dark brown, side-parted clean styling"
            face = "friendly approachable geometric face, expressive eyebrows"
            top = "teal crewneck sweater with neatly rolled cuffs"
            trousers = "dark navy flat-front trousers"
            shoes = "minimalist cream sneakers"
            palette = ["#0D9488 (Teal)", "#1E293B (Navy)", "#F8FAFC (Cream)", "#F59E0B (Amber)"]
            features = "natural conversational hand gestures, expressive eye-line"

        canonical_design = {
            "archetype": archetype,
            "hair": hair,
            "face": face,
            "body_proportions": "clean stylized geometric anatomy, proportional silhouette",
            "top": top,
            "trousers": trousers,
            "shoes": shoes,
            "color_palette": palette
        }

        prompt_anchor = (
            f"character {name}, {archetype}, {face}, {hair}, wearing {top} and {trousers}, "
            f"consistent character design, clean solid color palette"
        )

        record = {
            "character_id": char_id,
            "name": name,
            "archetype": archetype,
            "canonical_design": canonical_design,
            "prompt_anchor": prompt_anchor,
            "distinctive_features": features,
            "reference_assets": [],
            "approval_status": "spec_locked",
            "version": 1
        }

        self._character_registry[char_id] = record
        return record

    def resolve_environment_bible(self, topic_or_script: str) -> Dict[str, Any]:
        """
        Creates an environment registry for the story's locations.
        """
        lower = topic_or_script.lower()

        if any(w in lower for w in ["sugar", "dinner", "walk", "food", "kitchen", "eating", "meal"]):
            environments = [
                {
                    "environment_id": "env_dining_room",
                    "name": "Evening Dining Space",
                    "description": "Warm minimalist interior dining room with soft ambient pendant lamp and clean wooden table",
                    "lighting": "Warm 3000K diffused indoor evening light",
                    "palette": ["#FEF3C7 (Warm Glow)", "#78350F (Warm Wood)", "#1E293B (Soft Shadows)"],
                    "key_props": ["Dinner plate with finished meal", "Water glass", "Soft wooden dining chair"]
                },
                {
                    "environment_id": "env_bloodstream_infographic",
                    "name": "Bloodstream & Muscle Glucose Infographic",
                    "description": "Scientific vector cutaway diagram showing bloodstream capillaries, glucose particles, and muscle cells",
                    "lighting": "Clean infographic studio backdrop with glowing focal indicators",
                    "palette": ["#F8FAFC (Clean Light Canvas)", "#0D9488 (Teal Capillaries)", "#F43F5E (Glucose Nodes)", "#10B981 (Active Muscles)"],
                    "key_props": ["Capillary vessel cross-section", "Glowing glucose particles", "GLUT4 muscle receptor icons", "Flow arrows"]
                },
                {
                    "environment_id": "env_evening_neighborhood",
                    "name": "Peaceful Evening Walking Path",
                    "description": "Gentle suburban neighborhood sidewalk at twilight with warm streetlights and quiet residential greenery",
                    "lighting": "Twilight blue hour sky with soft golden streetlight puddles",
                    "palette": ["#1E293B (Twilight Blue)", "#0F766E (Evening Greenery)", "#FBBF24 (Streetlamp Gold)"],
                    "key_props": ["Paved sidewalk", "Subtle residential silhouette", "Curved pathway", "Gentle garden shrubs"]
                }
            ]
        elif any(w in lower for w in ["ac", "bedroom", "air", "headache", "co2", "sleep"]):
            environments = [
                {
                    "environment_id": "env_closed_bedroom",
                    "name": "Sealed Nighttime Bedroom",
                    "description": "Quiet minimalist bedroom with a mounted split AC unit gently humming, soft nightstand lamp",
                    "lighting": "Dim cool-blue night interior with subtle warm nightstand accent",
                    "palette": ["#0F172A (Midnight Slate)", "#38BDF8 (AC Cool Tone)", "#F1F5F9 (Bedding)"],
                    "key_props": ["Split air conditioner unit with louvers", "Bed with soft navy comforter", "Wall clock"]
                },
                {
                    "environment_id": "env_co2_infographic",
                    "name": "Air Circulation & CO2 Cutaway Diagram",
                    "description": "Cross-sectional room diagram displaying exhaled air recycling and CO2 parts-per-million gauge",
                    "lighting": "Flat graphic explainer background with glowing airflow path lines",
                    "palette": ["#F8FAFC (Clean Backdrop)", "#F43F5E (High CO2 Red)", "#0284C7 (Cold Air Blue)"],
                    "key_props": ["Airflow loop arrows", "Digital 2500 PPM gauge", "Recirculation indicator"]
                },
                {
                    "environment_id": "env_morning_window",
                    "name": "Open Morning Window",
                    "description": "Sunlit airy bedroom window with fresh morning breeze billowing sheer curtains gently",
                    "lighting": "Crisp golden morning sunlight streaming at a low angle",
                    "palette": ["#FEF3C7 (Morning Sunlight)", "#38BDF8 (Sky Blue)", "#FFFFFF (Clean Curtains)"],
                    "key_props": ["Cracked open bedroom door", "Window with outdoor morning view", "Fresh air flow lines"]
                }
            ]
        else:
            environments = [
                {
                    "environment_id": "env_main_interior",
                    "name": "Contemporary Explainer Studio Interior",
                    "description": "Modern minimalist studio interior with warm pastel architectural geometry and soft negative space",
                    "lighting": "Soft diffused three-point ambient lighting",
                    "palette": ["#FBF3EA (Pastel Beige)", "#1E293B (Deep Navy)", "#0D9488 (Teal Accent)"],
                    "key_props": ["Minimalist work desk", "Contemporary wall panel", "Ambient floor lamp"]
                },
                {
                    "environment_id": "env_infographic_stage",
                    "name": "Conceptual Diagram Canvas",
                    "description": "Clean, distraction-free technical diagram canvas highlighting system mechanisms and dynamic flow",
                    "lighting": "Neutral graphic display illumination",
                    "palette": ["#F8FAFC (Crisp Canvas)", "#0284C7 (Data Blue)", "#10B981 (Success Green)"],
                    "key_props": ["Flowchart nodes", "Directional vector arrows", "Metric callout cards"]
                }
            ]

        return {
            "environments": environments,
            "total_environments": len(environments)
        }


character_bible_manager = CharacterBibleManager()
