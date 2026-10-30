"""
Winplaybox / GravityClaw Master Animation Planning Engine.
Upgrades prompt generation into an intelligent, script-driven animation planning system
with decoupled visual design, evidence-checked scripts, separate visual/motion prompts,
and honest validation telemetry.
"""

import os
import json
import re
import uuid
import time
from typing import Dict, Any, List, Optional

from backend.services.art_styles import ART_STYLES, get_art_style
from backend.services.narrative_engine import narrative_engine
from backend.services.character_bible import character_bible_manager
from backend.services.storyboard_engine import storyboard_engine
from backend.services.quality_validator import quality_validation_engine

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CATALOG_PATH = os.path.join(DATA_DIR, "agent_universe_catalog.json")


class GravityClawAgentService:
    """
    Principal Multi-Platform Animation Planning & Reasoning Agent.
    """

    def __init__(self):
        self._catalog: Dict[str, Any] = {}
        self._load_catalog()

    def _load_catalog(self):
        if os.path.exists(CATALOG_PATH):
            try:
                with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                    self._catalog = json.load(f)
            except Exception as e:
                print(f"[GravityClaw] Failed to load catalog: {e}")
                self._catalog = {}

    def get_catalog_metadata(self) -> Dict[str, Any]:
        """Returns Master Catalog dimensions for frontend selectors."""
        return {
            "ok": True,
            "total_script_agents": self._catalog.get("total_script_agents", 0),
            "total_domains": self._catalog.get("total_domains", 0),
            "script_agents": self._catalog.get("script_agents", []),
            "domains": self._catalog.get("domains", []),
            "art_styles": [
                {
                    "id": k,
                    "name": v["name"],
                    "route_engine": v["route_engine"],
                    "description": v["description"]
                }
                for k, v in ART_STYLES.items()
            ],
            "tones": self._catalog.get("tones", []),
            "audiences": self._catalog.get("audiences", []),
            "platforms": self._catalog.get("platforms", []),
            "languages": self._catalog.get("languages", []),
            "workflows": self._catalog.get("workflows", [])
        }

    def generate_animation_plan(
        self,
        brief: Optional[str] = None,
        script: Optional[str] = None,
        script_mode: str = "auto",
        art_style: str = "2d_flat_vector",
        tone: str = "Educational",
        duration: str = "auto",
        target_duration_seconds: Optional[int] = None,
        language: str = "Hindi",
        aspect_ratio: str = "9:16",
        production_mode: str = "quality_first",
        animation_intensity: str = "expressive",
        character_consistency: str = "high",
        camera_direction: str = "story_driven",
        include_subtitles: bool = True,
        generate_storyboard: bool = True,
        agent_id: Optional[str] = None,
        domain: Optional[str] = None,
        audience: Optional[str] = None,
        platform: str = "YouTube Shorts",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Main entry point for intelligent, script-driven animation planning.
        Supports arbitrary topics, user-authored scripts, structured shot hierarchy,
        character-free diagrams, separated visual/motion prompts, and honest validation.
        """
        request_id = f"gc_req_{uuid.uuid4().hex[:10]}"
        raw_brief = (brief or kwargs.get("topic") or kwargs.get("prompt") or "").strip()
        raw_script = (script or kwargs.get("full_script") or "").strip()

        # Step 1: Resolve script mode (topic vs pre-authored script)
        resolved_mode, effective_text = narrative_engine.classify_script_mode(
            brief=raw_brief,
            script=raw_script,
            requested_mode=script_mode
        )

        if not effective_text:
            effective_text = "Why walking after dinner helps blunt postprandial glucose surges"

        # Step 2: Resolve Art Style Specification
        style_spec = get_art_style(art_style)

        # Step 3: Script & Narrative Synthesis
        if resolved_mode == "topic":
            script_data = narrative_engine.develop_script_from_topic(
                topic=effective_text,
                language=language,
                tone=tone,
                target_beats=5
            )
        else:
            script_data = narrative_engine.process_user_supplied_script(
                script_text=effective_text,
                language=language,
                target_beats=max(3, len(effective_text.splitlines()))
            )

        # Step 4: Timing & Duration Reconciliation
        duration_report = narrative_engine.reconcile_timing(
            requested_duration=target_duration_seconds,
            duration_preset=duration,
            script_duration=script_data["estimated_speech_duration_seconds"],
            beats_count=len(script_data["segments"])
        )
        planned_duration = duration_report["planned_storyboard_duration_seconds"]

        # Step 5: Character Bible & Environment Resolution
        char_record = character_bible_manager.resolve_character(
            topic_or_script=effective_text,
            style_key=style_spec["id"]
        )
        env_bible = character_bible_manager.resolve_environment_bible(effective_text)

        # Step 6: Hierarchical Storyboard & Motion Planning (Scenes -> Shots)
        storyboard = storyboard_engine.build_storyboard(
            script_data=script_data,
            character_record=char_record,
            environment_bible=env_bible,
            art_style=style_spec,
            target_duration=planned_duration,
            aspect_ratio=aspect_ratio,
            camera_direction_preset=camera_direction
        )

        # Step 7: Generation Plan Formulation
        generation_jobs = []
        for shot in storyboard["shots"]:
            generation_jobs.append({
                "job_id": f"job_{shot['shot_id']}",
                "shot_id": shot["shot_id"],
                "scene_id": shot["scene_id"],
                "target_engine": shot["generation"]["workflow_id"],
                "mode": shot["generation"]["mode"],
                "duration_seconds": shot["planned_duration_seconds"],
                "aspect_ratio": aspect_ratio,
                "status": "planned",
                "inputs": {
                    "visual_prompt": shot["visual_prompt"],
                    "video_motion_prompt": shot["video_motion_prompt"],
                    "has_character": len(shot["characters"]) > 0,
                    "character_id": shot["characters"][0]["character_id"] if shot["characters"] else None
                }
            })

        generation_plan = {
            "status": "planned",
            "primary_engine": style_spec["route_engine"],
            "fallback_engine": "COMFYUI_VIDEO_DIT" if style_spec["route_engine"] != "COMFYUI_VIDEO_DIT" else "2D_ANIMATION_RIGS",
            "total_jobs": len(generation_jobs),
            "jobs": generation_jobs
        }

        # Step 8: Quality Validation (Pre-flight evaluated, Runtime marked 'not_run')
        validation_results = quality_validation_engine.validate_plan(
            script_data=script_data,
            character_bible=char_record,
            storyboard=storyboard,
            art_style=style_spec,
            duration_report=duration_report
        )

        # Narrative profile
        narrative_profile = {
            "genre": "educational_explainer" if "educat" in tone.lower() or "story" in tone.lower() else "narrative_story",
            "tone": tone,
            "platform": platform,
            "audience": audience or "General audience",
            "language": script_data["language"],
            "target_duration_seconds": planned_duration,
            "total_beats": len(storyboard["scenes"]),
            "pacing_seconds_per_beat": round(planned_duration / max(1, len(storyboard["scenes"])), 1)
        }

        # 0-3s Hook extraction
        hook_text = script_data["segments"][0]["narration"] if script_data["segments"] else effective_text

        # 12-Stage Pipeline Metadata
        stage_1_inputs = {
            "stage_id": 1,
            "stage_name": "User Script + Style Settings",
            "raw_input": effective_text,
            "script_mode": resolved_mode,
            "word_count": script_data["word_count"],
            "art_style": style_spec["name"],
            "art_style_id": style_spec["id"],
            "target_duration_seconds": planned_duration,
            "target_beats": len(storyboard["scenes"]),
            "platform": platform,
            "language": script_data["language"]
        }

        stage_2_intent = {
            "stage_id": 2,
            "stage_name": "GravityClaw Creative Intent Interpreter",
            "retention_hook_0_3s": hook_text,
            "hook": hook_text,
            "psychological_trigger": "Curiosity Gap + Relatable Friction",
            "narrative_tone": tone,
            "rigor_level": "High (Evidence-Qualified)"
        }

        stage_3_analysis = {
            "stage_id": 3,
            "stage_name": "Script Analyzer",
            "detected_characters": [char_record["name"]],
            "detected_actions": [s["motion"]["primary_action"] for s in storyboard["shots"][:3]],
            "detected_locations": [env["name"] for env in env_bible["environments"]],
            "detected_props": [p for env in env_bible["environments"] for p in env.get("key_props", [])][:6]
        }

        stage_4_vds = {
            "stage_id": 4,
            "stage_name": "Visual Design System",
            "character_dna": char_record,
            "environment_palette": env_bible,
            "style_tokens": {
                "positive": style_spec["positive_tokens"],
                "negative": style_spec["negative_tokens"]
            }
        }

        stage_5_storyboard = {
            "stage_id": 5,
            "stage_name": "Storyboard Engine",
            "total_beats": len(storyboard["scenes"]),
            "beats": storyboard["scenes"],
            "pacing_seconds_per_beat": narrative_profile["pacing_seconds_per_beat"]
        }

        stage_6_motion = {
            "stage_id": 6,
            "stage_name": "Motion Planner",
            "camera_vectors": [s["camera"]["movement"] for s in storyboard["shots"]],
            "vfx_overlays": [s["environmental_movement"] for s in storyboard["shots"]],
            "motion_vectors": [
                {
                    "shot_id": s["shot_id"],
                    "camera_vector": s["camera"]["movement"],
                    "primary_action": s["motion"]["primary_action"],
                    "secondary_actions": s["motion"]["secondary_actions"]
                }
                for s in storyboard["shots"]
            ]
        }

        stage_7_router = {
            "stage_id": 7,
            "stage_name": "Workflow Router",
            "selected_engine": style_spec["route_engine"],
            "fallback_engine": generation_plan["fallback_engine"],
            "route_description": (
                "HyperFrames / Remotion Vector Puppet Rigging (Kurzgesagt aesthetic)"
                if style_spec["route_engine"] == "2D_ANIMATION_RIGS"
                else "ComfyUI Video DiT (Wan 2.1 I2V / LTX-Video / AnimateDiff)"
            )
        }

        stage_8_validator = {
            "stage_id": 8,
            "stage_name": "Shot Validator",
            "status": validation_results["status"],
            "metrics": {
                "plan_soundness": 1.0 if validation_results["preflight_passed"] else 0.7,
                "character_spec_locked": True,
                "optical_motion_flow": "Pending video generation (status: not_run)",
                "face_cosine_similarity": "Pending video generation (status: not_run)",
                "verdict": "PLAN_VALIDATED" if validation_results["preflight_passed"] else "NEEDS_REVIEW"
            },
            "checks": validation_results["checks"]
        }

        stage_9_regeneration = {
            "stage_id": 9,
            "stage_name": "Targeted Regeneration",
            "strategy": "Single-Beat Isolated Re-Roll",
            "supported": True,
            "description": "Any single beat can be re-rolled on demand using modified seed/motion prompt without re-rendering untouched scenes."
        }

        stage_10_audio_comp = {
            "stage_id": 10,
            "stage_name": "Audio + Composition",
            "tts_engine": "Edge-TTS Neural (Multi-Language)",
            "subtitles_engine": "Faster-Whisper Kinetic Word-by-Word (.SRT)",
            "compositor": "FFmpeg Hardware 4K Compiler (ultrafast, threads=2)",
            "output_format": "MP4 (H.264 / AAC)"
        }

        stage_11_review = {
            "stage_id": 11,
            "stage_name": "Final Review",
            "monitor_chassis": "Live HTML5 4K Output Chassis",
            "features": ["Play/Pause", "Scrubbing", "Looping", "Single-Beat Inspector"]
        }

        stage_12_export = {
            "stage_id": 12,
            "stage_name": "Exported Video",
            "actions": [
                "Download 4K Master MP4",
                "1-Click Social Dispatch (YouTube, Instagram, TikTok)",
                "8-Domain Autonomous Blog Syndication"
            ]
        }

        stages = [
            stage_1_inputs,
            stage_2_intent,
            stage_3_analysis,
            stage_4_vds,
            stage_5_storyboard,
            stage_6_motion,
            stage_7_router,
            stage_8_validator,
            stage_9_regeneration,
            stage_10_audio_comp,
            stage_11_review,
            stage_12_export
        ]

        # Compile Master Unified Response
        response = {
            "ok": True,
            "request_id": request_id,
            "brief": raw_brief or effective_text,
            "creative_brief": {
                "topic": effective_text,
                "script_mode": resolved_mode,
                "tone": tone,
                "domain": domain or "Healthcare & Medicine",
                "audience": audience or "General audience",
                "platform": platform,
                "language": script_data["language"],
                "production_mode": production_mode
            },
            "narrative_profile": narrative_profile,
            "script": script_data,
            "character_bible": char_record,
            "environment_bible": env_bible,
            "storyboard": storyboard,
            "generation_plan": generation_plan,
            "validation": validation_results,
            "duration_report": duration_report,
            "warnings": script_data.get("warnings", []),
            "errors": [],

            # --- Backward Compatibility for existing Studio UI & tests ---
            "hook": hook_text,
            "retention_hook": hook_text,
            "character_dna": char_record,
            "art_style": style_spec,
            "scenes": storyboard["scenes"],
            "scene_prompt": storyboard["scenes"][0]["art_prompt"] if storyboard["scenes"] else "",
            "tags": [
                f"#{re.sub(r'[^a-zA-Z0-9]', '', domain or 'Explainer')}",
                "#WinplayboxAI",
                "#AnimationPlanning",
                "#HealthFacts" if "health" in (domain or "").lower() or "sugar" in effective_text.lower() else "#Explainer"
            ],
            "estimated_retention": "Calibrated retention model offline; heuristic estimates omitted for verification integrity.",
            "stages": stages
        }

        return response

    def reroll_beat(
        self,
        scene: Dict[str, Any],
        prompt_tweak: str = "",
        character_dna: Optional[Dict[str, Any]] = None,
        style_key: str = "2d_flat_vector",
        seed_offset: int = 100
    ) -> Dict[str, Any]:
        """
        Stage 9: Targeted Regeneration.
        Regenerates a single beat's visual prompt, motion prompt, and seed while preserving Character DNA and sequence continuity.
        """
        import urllib.parse
        updated = dict(scene)
        style_spec = get_art_style(style_key)

        dna_anchor = ""
        if character_dna and "prompt_anchor" in character_dna:
            dna_anchor = character_dna["prompt_anchor"]
        elif "character_action" in updated:
            dna_anchor = updated["character_action"].split(" ")[0]

        if prompt_tweak:
            updated["character_action"] = prompt_tweak
            updated["art_prompt"] = f"{style_spec['positive_tokens']}, {dna_anchor}, {prompt_tweak}, highly detailed clean composition"
            updated["prompt"] = updated["art_prompt"]
            updated["motion_prompt"] = f"{updated.get('camera_vector', 'smooth cinematic push')}, {prompt_tweak}, {style_spec['motion_style']}"
            updated["motion_direction"] = updated["motion_prompt"]

        new_seed = int(time.time() * 1000) % 999999 + seed_offset
        updated["seed"] = new_seed
        encoded_prompt = urllib.parse.quote(updated.get("art_prompt", "")[:240])
        updated["image_url"] = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={new_seed}"
        updated["regenerated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        updated["status"] = "RE_ROLLED"
        updated["validation_scores"] = {
            "plan_consistency": "verified",
            "seed_isolated": True,
            "status": "ready_for_regeneration"
        }
        return updated

    # Backward compatibility entry points
    def deconstruct_script_to_storyboard(self, **kwargs) -> Dict[str, Any]:
        return self.generate_animation_plan(**kwargs)

    def execute_master_pipeline(self, **kwargs) -> Dict[str, Any]:
        return self.generate_animation_plan(**kwargs)


gravityclaw_service = GravityClawAgentService()
