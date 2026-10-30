"""
Winplaybox / GravityClaw Storyboard Engine.
Generates structured scenes and shots with explicit motion planning,
separated visual and motion prompts, character-free infographic support,
and workflow routing adapters (2D Rigs vs ComfyUI Video DiT).
"""

from typing import Dict, Any, List, Optional
import math


class StoryboardEngine:
    """
    Synthesizes structured hierarchical storyboards (Scenes -> Shots)
    with executable motion plans and separate visual/motion prompts.
    """

    def __init__(self):
        pass

    def build_storyboard(
        self,
        script_data: Dict[str, Any],
        character_record: Dict[str, Any],
        environment_bible: Dict[str, Any],
        art_style: Dict[str, Any],
        target_duration: float,
        aspect_ratio: str = "9:16",
        camera_direction_preset: str = "story_driven"
    ) -> Dict[str, Any]:
        """
        Builds the complete hierarchical storyboard containing scenes and structured shots.
        """
        segments = script_data.get("segments", [])
        if not segments:
            segments = [{
                "segment_id": "seg_001",
                "beat_number": 1,
                "beat_role": "Core Narrative Beat",
                "narration": script_data.get("full_script", "Visual scene execution"),
                "estimated_speech_seconds": max(5.0, target_duration)
            }]

        total_segments = len(segments)
        environments = environment_bible.get("environments", [])
        primary_env = environments[0] if environments else {
            "environment_id": "env_default",
            "name": "Minimalist Studio",
            "lighting": "Diffused studio illumination"
        }
        diagram_env = environments[1] if len(environments) > 1 else primary_env
        outdoor_env = environments[2] if len(environments) > 2 else primary_env

        # Allocate planned duration across shots to match target duration
        total_speech = sum(s["estimated_speech_seconds"] for s in segments)
        if total_speech <= 0:
            total_speech = target_duration

        scenes = []
        shots = []
        current_time_offset = 0.0

        for idx, seg in enumerate(segments):
            scene_id = f"scene_{idx + 1:03d}"
            shot_id = f"shot_{idx + 1:03d}"
            beat_role = seg.get("beat_role", f"Beat {idx + 1}")
            narration = seg.get("narration", "")

            # Compute shot duration proportionally so sum(durations) == target_duration
            weight = seg["estimated_speech_seconds"] / total_speech
            shot_dur = round(max(3.5, target_duration * weight), 1)

            # Determine whether this shot needs the protagonist or is an infographic/diagram
            is_infographic = (
                "infographic" in beat_role.lower() or
                "mechanism" in beat_role.lower() or
                idx == 2 and total_segments >= 4
            )
            is_resolution_or_action = idx >= total_segments - 2

            if is_infographic:
                shot_characters = []
                assigned_env = diagram_env
                composition = "Centrally aligned scientific diagrammatic view, clean high negative space, 9:16 vertical layout"
                cam_movement = "static_central_focus"
                cam_type = "infographic_cutaway"
                cam_dir = "inward_zoom"
                start_state = "Clean vector anatomical cross-section showing resting baseline"
                primary_action = "Animated directional flow arrows indicate dynamic glucose transport into muscle cells without insulin dependency"
                secondary_actions = [
                    "GLUT4 glucose transporters illuminate green",
                    "Bloodstream glucose counter gently decrements",
                    "Active leg muscle fibers contract in subtle rhythm"
                ]
                end_state = "Balanced metabolic flow visualization with positive indicator badge"
                env_movement = "Pulsing glowing transport paths, soft particle drift"
                generation_mode = "infographic_compositor"
                workflow_id = "hyperframes_2d_vector" if art_style["route_engine"] == "2D_ANIMATION_RIGS" else "comfyui_wan21_i2v"

                # Visual prompt DOES NOT contain character prompt anchor!
                visual_prompt = (
                    f"{art_style['positive_tokens']}, "
                    f"educational infographic cross-section diagram, {assigned_env['name']}, "
                    f"translucent anatomical cutaway, glowing biological flow arrows, "
                    f"clean vector indicators, zero human faces, high negative space, pristine scientific visualization"
                )
                motion_prompt = (
                    f"Smooth 2D kinetic diagram animation, directional arrows flowing along capillary path, "
                    f"glowing particles docking into receptors, static camera with subtle 2% optical punch-in, no camera shake"
                )

            elif is_resolution_or_action:
                shot_characters = [{
                    "character_id": character_record["character_id"],
                    "name": character_record["name"],
                    "action": "walks at a calm, relaxed pace along the quiet twilight path with an uplifted, healthy expression",
                    "expression": "peaceful, confident, relaxed"
                }]
                assigned_env = outdoor_env
                composition = "Full-body tracking shot, character moving left to right at medium distance"
                cam_movement = "gentle_lateral_tracking"
                cam_type = "wide_full_shot"
                cam_dir = "right"
                start_state = f"{character_record['name']} walking at the left-third of the tranquil evening pathway"
                primary_action = f"{character_record['name']} takes natural relaxed strides while breathing in crisp evening air"
                secondary_actions = [
                    "Arms swing smoothly in natural walking cadence",
                    "Clothing hem sways subtly with stride inertia",
                    "Dusk twilight sky glows softly behind quiet residential greenery"
                ]
                end_state = f"{character_record['name']} centered in frame, glancing forward with serene contentment"
                env_movement = "Soft ambient streetlamp glow, gentle rustling leaves in evening breeze"
                generation_mode = "2d_animation_rig" if art_style["route_engine"] == "2D_ANIMATION_RIGS" else "image_to_video"
                workflow_id = "hyperframes_2d_vector" if art_style["route_engine"] == "2D_ANIMATION_RIGS" else "comfyui_wan21_i2v"

                visual_prompt = (
                    f"{art_style['positive_tokens']}, "
                    f"{character_record['prompt_anchor']}, "
                    f"walking along {assigned_env['name']}, serene dusk atmosphere, warm streetlight illumination, "
                    f"clean full body composition, 9:16 portrait orientation"
                )
                motion_prompt = (
                    f"Smooth character walk cycle, natural arm swing, subtle secondary clothing motion, "
                    f"camera smoothly tracks character moving rightwards, steady lateral glide, 24fps fluid motion"
                )

            else:
                # Character in initial inciting context (e.g. sitting at dining table or living room)
                shot_characters = [{
                    "character_id": character_record["character_id"],
                    "name": character_record["name"],
                    "action": "seated comfortably after dinner, resting back with relatable fullness and heavy eyelids",
                    "expression": "slightly groggy, relatable tired smile"
                }]
                assigned_env = primary_env
                composition = "Medium shot at eye-level, character seated at dining table with meal remnants"
                cam_movement = "slow_cinematic_push"
                cam_type = "medium_shot"
                cam_dir = "forward"
                start_state = f"{character_record['name']} seated at the table, finishing the last bite of evening dinner"
                primary_action = f"{character_record['name']} gently puts down cutlery and touches forehead with tired sigh"
                secondary_actions = [
                    "Chest rises and falls with relaxed deep breath",
                    "Warm pendant light casts soft natural shadows across table",
                    "Water glass catches warm table reflection"
                ]
                end_state = f"{character_record['name']} looking up thoughtfully toward the window"
                env_movement = "Subtle warmth of interior lighting, stationary room props"
                generation_mode = "2d_animation_rig" if art_style["route_engine"] == "2D_ANIMATION_RIGS" else "image_to_video"
                workflow_id = "hyperframes_2d_vector" if art_style["route_engine"] == "2D_ANIMATION_RIGS" else "comfyui_wan21_i2v"

                visual_prompt = (
                    f"{art_style['positive_tokens']}, "
                    f"{character_record['prompt_anchor']}, "
                    f"seated in {assigned_env['name']}, warm ambient evening lighting, "
                    f"clean medium shot, highly detailed clean composition, 9:16 portrait"
                )
                motion_prompt = (
                    f"Slow push-in dolly (0 to {shot_dur}s), character blinks naturally and lowers hands to table, "
                    f"subtle chest breathing dynamics, zero harsh camera jitter"
                )

            shot_data = {
                "shot_id": shot_id,
                "scene_id": scene_id,
                "shot_number": idx + 1,
                "source_script_segment": narration,
                "narration_segment_ids": [seg.get("segment_id", f"seg_{idx + 1:03d}")],
                "planned_duration_seconds": shot_dur,
                "start_time_seconds": round(current_time_offset, 2),
                "end_time_seconds": round(current_time_offset + shot_dur, 2),
                "characters": shot_characters,
                "environment": {
                    "environment_id": assigned_env["environment_id"],
                    "name": assigned_env["name"],
                    "lighting": assigned_env["lighting"]
                },
                "props": assigned_env.get("key_props", []),
                "composition": composition,
                "camera": {
                    "shot_type": cam_type,
                    "movement": cam_movement,
                    "direction": cam_dir,
                    "aspect_ratio": aspect_ratio
                },
                "motion": {
                    "start_state": start_state,
                    "primary_action": primary_action,
                    "secondary_actions": secondary_actions,
                    "end_state": end_state
                },
                "environmental_movement": env_movement,
                "visual_prompt": visual_prompt,
                "video_motion_prompt": motion_prompt,
                "generation": {
                    "mode": generation_mode,
                    "workflow_id": workflow_id,
                    "status": "planned"
                }
            }

            scene_data = {
                "scene_id": scene_id,
                "scene_number": idx + 1,
                "beat_title": f"Beat {idx + 1}: {beat_role}",
                "beat_role": beat_role,
                "narration": narration,
                "shot_count": 1,
                "shots": [shot_id],
                "duration_seconds": shot_dur,
                # Legacy fields for backward compatibility with 4K Studio
                "beat": f"Beat {idx + 1}: {beat_role}",
                "art_prompt": visual_prompt,
                "prompt": visual_prompt,
                "motion_direction": motion_prompt,
                "character_action": primary_action,
                "camera_vector": f"{cam_movement} ({cam_type})",
                "character_physics": "; ".join(secondary_actions),
                "vfx_overlay": env_movement,
                "estimated_duration_sec": shot_dur
            }

            scenes.append(scene_data)
            shots.append(shot_data)
            current_time_offset += shot_dur

        return {
            "total_scenes": len(scenes),
            "total_shots": len(shots),
            "planned_duration_seconds": round(current_time_offset, 2),
            "scenes": scenes,
            "shots": shots
        }


storyboard_engine = StoryboardEngine()
