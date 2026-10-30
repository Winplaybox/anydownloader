"""
Unit and Integration Test Suite for Winplaybox GravityClaw Animation Planning Engine.
Validates all 16 Phase 13 mission requirements.
"""

import pytest
import os
import sys

# Ensure backend is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.gravityclaw_agent import gravityclaw_service
from backend.services.art_styles import ART_STYLES, get_art_style
from backend.services.narrative_engine import narrative_engine
from backend.services.character_bible import character_bible_manager
from backend.services.storyboard_engine import storyboard_engine
from backend.services.quality_validator import quality_validation_engine
from backend.services.video_producer import video_producer


def test_1_arbitrary_user_provided_topic():
    """1. Arbitrary user-provided topic generates complete script and storyboard."""
    res = gravityclaw_service.generate_animation_plan(
        brief="How quantum computers use superposition to solve cryptography",
        language="English",
        art_style="3d_scientific_medical",
        tone="Educational"
    )
    assert res["ok"] is True
    assert res["creative_brief"]["script_mode"] == "topic"
    assert len(res["script"]["segments"]) >= 4
    assert res["script"]["word_count"] > 30
    assert "superposition" in res["script"]["full_script"].lower() or "quantum" in res["script"]["full_script"].lower()


def test_2_complete_user_provided_script():
    """2. Complete user-provided script is preserved without being replaced by an invented story."""
    user_script = (
        "First, you mix flour, salt, and yeast into a warm bowl. "
        "Next, knead the dough firmly for eight minutes until smooth and elastic. "
        "Then, let it rise in a warm spot until doubled in size. "
        "Finally, bake at 450 degrees until golden and hollow sounding."
    )
    res = gravityclaw_service.generate_animation_plan(
        script=user_script,
        script_mode="script",
        language="English",
        art_style="storybook"
    )
    assert res["ok"] is True
    assert res["creative_brief"]["script_mode"] == "script"
    assert res["script"]["full_script"] == user_script
    # Check that segments contain the actual sentences
    assert any("flour" in seg["narration"] for seg in res["script"]["segments"])
    assert any("bake" in seg["narration"] for seg in res["script"]["segments"])


def test_3_hindi_narration_generation():
    """3. Hindi narration generation produces authentic, natural Hindi phrasing."""
    res = gravityclaw_service.generate_animation_plan(
        brief="Why eating walking after dinner prevents blood sugar spikes",
        language="Hindi",
        art_style="2d_flat_vector"
    )
    assert res["ok"] is True
    hindi_text = res["script"]["full_script"]
    # Check for natural Devanagari script and grammatical structure
    assert "डिनर" in hindi_text or "खाना" in hindi_text
    assert "ग्लूकोज" in hindi_text or "ब्लड शुगर" in hindi_text
    assert "वॉक" in hindi_text or "मांसपेशियां" in hindi_text
    # Ensure it's not simply an English sentence prefixed with Hindi
    assert not hindi_text.startswith("अगर आप भी ये ग़लती रोज़ कर रहे हैं—तो रुकिए, सच जानकर होश उड़ जाएंगे: Why eating walking")


def test_4_different_narration_for_different_story_beats():
    """4. Different narration for different story beats (no repeated brief text)."""
    res = gravityclaw_service.generate_animation_plan(
        brief="Why eating walking after dinner prevents blood sugar spikes",
        language="Hindi",
        art_style="2d_flat_vector"
    )
    segments = res["script"]["segments"]
    assert len(segments) >= 4

    narrations = [s["narration"].strip() for s in segments]
    # All narrations must be distinct
    assert len(set(narrations)) == len(narrations)
    # None of them should be equal to the raw brief
    for n in narrations:
        assert n != "Why eating walking after dinner prevents blood sugar spikes"


def test_5_duration_reconciliation():
    """5. Duration reconciliation between speech, target seconds, and storyboard holds."""
    res = gravityclaw_service.generate_animation_plan(
        brief="Why eating walking after dinner prevents blood sugar spikes",
        target_duration_seconds=60,
        language="English",
        art_style="2d_flat_vector"
    )
    dur_rep = res["duration_report"]
    assert dur_rep["requested_duration_seconds"] == 60
    assert dur_rep["estimated_narration_duration_seconds"] > 0
    assert dur_rep["planned_storyboard_duration_seconds"] > 0
    # Sum of shot durations must equal planned storyboard duration
    total_shots_duration = sum(s["planned_duration_seconds"] for s in res["storyboard"]["shots"])
    assert abs(total_shots_duration - dur_rep["planned_storyboard_duration_seconds"]) < 0.5


def test_6_character_reference_persistence():
    """6. Character reference persistence with canonical design specs."""
    res = gravityclaw_service.generate_animation_plan(
        brief="A day in the life of a software engineer fixing race conditions",
        art_style="2d_flat_vector"
    )
    char = res["character_bible"]
    assert "character_id" in char
    assert "name" in char
    assert "canonical_design" in char
    design = char["canonical_design"]
    assert "hair" in design
    assert "face" in design
    assert "top" in design
    assert "trousers" in design
    assert "color_palette" in design
    assert char["approval_status"] == "spec_locked"


def test_7_character_free_infographic_shots():
    """7. Character-free infographic shots do not inject protagonist prompt anchors."""
    res = gravityclaw_service.generate_animation_plan(
        brief="Why eating walking after dinner prevents blood sugar spikes",
        art_style="2d_flat_vector"
    )
    shots = res["storyboard"]["shots"]
    # Shot 3 is the physiological mechanism diagram
    diagram_shot = shots[2]
    assert len(diagram_shot["characters"]) == 0
    # Ensure visual prompt doesn't have Rohan or protagonist name
    assert "Rohan" not in diagram_shot["visual_prompt"]
    assert "named" not in diagram_shot["visual_prompt"]
    assert "wearing" not in diagram_shot["visual_prompt"]
    assert "infographic" in diagram_shot["visual_prompt"] or "diagram" in diagram_shot["visual_prompt"]


def test_8_style_consistency():
    """8. Style consistency across all shots without contradictory instructions."""
    res = gravityclaw_service.generate_animation_plan(
        brief="Deep sea bioluminescent creatures",
        art_style="3d_scientific_medical"
    )
    style = res["art_style"]
    assert style["id"] == "3d_scientific_medical"
    assert style["route_engine"] == "COMFYUI_VIDEO_DIT"
    for shot in res["storyboard"]["shots"]:
        assert "3D medical animation" in shot["visual_prompt"] or "octane render" in shot["visual_prompt"]
        assert "flat 2D vector" not in shot["visual_prompt"]


def test_9_motion_specification_generation():
    """9. Motion-specification generation distinguishes start, action, end states and separates visual prompt."""
    res = gravityclaw_service.generate_animation_plan(
        brief="Morning meditation and mindfulness routines",
        art_style="2d_flat_vector"
    )
    for shot in res["storyboard"]["shots"]:
        motion = shot["motion"]
        assert "start_state" in motion and len(motion["start_state"]) > 5
        assert "primary_action" in motion and len(motion["primary_action"]) > 5
        assert "secondary_actions" in motion and isinstance(motion["secondary_actions"], list)
        assert "end_state" in motion and len(motion["end_state"]) > 5
        # Visual prompt and motion prompt must be distinct
        assert shot["visual_prompt"] != shot["video_motion_prompt"]
        assert len(shot["video_motion_prompt"]) > 10


def test_10_model_and_workflow_availability():
    """10. Real model and workflow server availability check."""
    res = gravityclaw_service.generate_animation_plan(
        brief="The solar system formation",
        art_style="3d_pixar"
    )
    checks = res["validation"]["checks"]
    wf_check = next((c for c in checks if "CHK_WORKFLOW_SERVER" in c["check_id"]), None)
    assert wf_check is not None
    # Must report passed or simulated_fallback honestly based on port 8188 socket
    assert wf_check["status"] in ["passed", "simulated_fallback"]
    assert wf_check["category"] == "infrastructure"


def test_11_failed_video_generation_handling():
    """11. Video producer handles empty or non-existent assets safely."""
    fake_scenes = [{"asset": "non_existent_file_12345.png", "prompt": "Invalid image"}]
    # Calling assemble_story_video with empty/invalid images falls back safely
    res = video_producer.assemble_story_video(
        audio_path="invalid_audio_path_xyz.mp3",
        scenes=fake_scenes,
        resolution="720x1280"
    )
    # Handled without unhandled exception crashing the process
    assert isinstance(res, dict)
    assert res.get("ok") is False or "error" in res


def test_12_missing_output_artifacts_handling():
    """12. Video producer missing output artifacts handling."""
    res = video_producer.assemble_reel_video(
        audio_path="fake_non_existent.mp3",
        scenes=[]
    )
    assert res.get("ok") is False
    assert "error" in res


def test_13_validation_runtime_checks_not_run():
    """13. Runtime checks (optical flow, face cosine, A/V sync) are marked 'not_run' with confidence None."""
    res = gravityclaw_service.generate_animation_plan(
        brief="Why eating walking after dinner prevents blood sugar spikes"
    )
    checks = res["validation"]["checks"]
    runtime_checks = [c for c in checks if c["category"] == "runtime_post_render"]
    assert len(runtime_checks) >= 3
    for rc in runtime_checks:
        assert rc["status"] == "not_run"
        assert rc["confidence"] is None
        assert "Pending" in rc["evidence"]


def test_14_unsupported_retention_predictions_omitted():
    """14. Fabricated retention percentages are omitted or flagged as uncalibrated."""
    res = gravityclaw_service.generate_animation_plan(
        brief="Why eating walking after dinner prevents blood sugar spikes"
    )
    val = res["validation"]
    assert val["calibrated_retention"] is None
    assert "offline" in val["retention_note"].lower() or "omitted" in val["retention_note"].lower()
    # Ensure legacy field doesn't make fake specific statistical claims like 94.6%
    assert "94.6%" not in res["estimated_retention"]


def test_15_backward_compatibility_for_existing_consumers():
    """15. Backward compatibility for legacy callers expecting scenes, hook, script, art_style, stages."""
    res = gravityclaw_service.generate_animation_plan(
        brief="Why eating walking after dinner prevents blood sugar spikes"
    )
    assert "hook" in res
    assert "retention_hook" in res
    assert "scenes" in res
    assert isinstance(res["scenes"], list) and len(res["scenes"]) > 0
    assert "scene_prompt" in res
    assert "character_dna" in res
    assert "art_style" in res
    assert "stages" in res and len(res["stages"]) == 12
    # Check scene beat structure has legacy fields
    s0 = res["scenes"][0]
    assert "beat" in s0
    assert "art_prompt" in s0
    assert "character_action" in s0
    assert "estimated_duration_sec" in s0


def test_16_healthcare_regression_benchmark():
    """16. Complete end-to-end regression benchmark on user's exact health topic."""
    input_payload = {
        "brief": "Why eating walking after dinner prevents blood sugar spikes",
        "art_style": "2d_flat_vector",
        "agent_id": "SCR-0003",
        "tone": "Story-driven",
        "duration": "extended",
        "language": "Hindi"
    }
    res = gravityclaw_service.generate_animation_plan(**input_payload)

    # A: Success and ID
    assert res["ok"] is True
    assert res["request_id"].startswith("gc_req_")

    # B: Natural Hindi script with distinct narrative segments
    script_obj = res["script"]
    assert script_obj["language"] == "Hindi"
    assert len(script_obj["segments"]) >= 4
    texts = [seg["narration"] for seg in script_obj["segments"]]
    assert len(set(texts)) == len(texts)

    # C: Medical qualification & disclaimer
    assert len(res["warnings"]) > 0
    assert "Health & Medical Disclaimer" in res["warnings"][0]

    # D: Infographic diagram beat has no protagonist
    diagram_shot = res["storyboard"]["shots"][2]
    assert len(diagram_shot["characters"]) == 0
    assert "Rohan" not in diagram_shot["visual_prompt"]

    # E: Character shots have consistent character
    char_shots = [s for s in res["storyboard"]["shots"] if len(s["characters"]) > 0]
    assert len(char_shots) >= 2
    for cs in char_shots:
        assert cs["characters"][0]["character_id"] == "char_rohan_explainer_001"

    # F: Duration reconciliation
    assert res["duration_report"]["planned_storyboard_duration_seconds"] > 0

    # G: Quality validation status is honest
    val = res["validation"]
    assert val["preflight_passed"] is True
    assert val["pending_runtime_checks"] >= 3
