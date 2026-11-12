"""ffmpeg helpers: probe, frame/audio extraction and the final render + audio mastering."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from typing import Any, Callable, Dict, List, Optional, Tuple

FONTS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", "fonts"))
X264_PRESET = os.environ.get("EDITOR_X264_PRESET", "veryfast")
X264_CRF = os.environ.get("EDITOR_X264_CRF", "21")
LONG_SIDE = int(os.environ.get("EDITOR_OUTPUT_LONG_SIDE", "1920"))
FFMPEG_THREADS = os.environ.get("EDITOR_FFMPEG_THREADS", "0")


class RenderError(Exception):
    pass


def _bin(name: str) -> str:
    p = shutil.which(name)
    if p:
        return p
    try:  # static-ffmpeg is already a dependency of the job manager
        import static_ffmpeg

        static_ffmpeg.add_paths()
        p = shutil.which(name)
    except Exception:
        p = None
    if not p:
        raise RenderError(f"{name} not found on server")
    return p


def run(cmd: List[str], timeout: int = 900) -> subprocess.CompletedProcess:
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if r.returncode != 0:
        tail = r.stderr.decode(errors="ignore").strip().splitlines()[-6:]
        raise RenderError("ffmpeg failed: " + " | ".join(tail))
    return r


def probe(path: str) -> Dict[str, Any]:
    r = run([_bin("ffprobe"), "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path], 60)
    info = json.loads(r.stdout or b"{}")
    v = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
    a = next((s for s in info.get("streams", []) if s.get("codec_type") == "audio"), None)
    if not v:
        raise RenderError("No video stream found in the upload.")
    w, h = int(v.get("width") or 0), int(v.get("height") or 0)
    rot = 0
    for sd in v.get("side_data_list") or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    rot = rot or int(float((v.get("tags") or {}).get("rotate", 0) or 0))
    if abs(rot) % 180 == 90:
        w, h = h, w
    dur = float(info.get("format", {}).get("duration") or v.get("duration") or 0)
    num, _, den = str(v.get("avg_frame_rate") or "30/1").partition("/")
    try:
        fps = float(num) / float(den or 1)
    except (ValueError, ZeroDivisionError):
        fps = 30.0
    return {"duration": round(dur, 3), "width": w, "height": h, "fps": round(fps, 2), "has_audio": a is not None,
            "codec": v.get("codec_name")}


def output_size(src_w: int, src_h: int, fmt: str) -> Tuple[int, int]:
    if fmt == "vertical":
        return LONG_SIDE * 9 // 16 // 2 * 2, LONG_SIDE
    if src_w >= src_h:
        w, h = LONG_SIDE, int(round(LONG_SIDE * src_h / max(1, src_w)))
    else:
        w, h = int(round(LONG_SIDE * src_w / max(1, src_h))), LONG_SIDE
    return max(2, w // 2 * 2), max(2, h // 2 * 2)


def extract_frames(path: str, out_dir: str, duration: float, n: int = 8) -> List[Tuple[float, bytes]]:
    os.makedirs(out_dir, exist_ok=True)
    n = max(3, min(n, 12))
    times = [round(duration * (i + 0.5) / n, 2) for i in range(n)]
    frames = []
    for i, t in enumerate(times):
        dst = os.path.join(out_dir, f"f{i:02d}.jpg")
        try:
            run([_bin("ffmpeg"), "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1",
                 "-vf", "scale='if(gt(iw,ih),640,-2)':'if(gt(iw,ih),-2,640)'", "-q:v", "5", dst], 60)
            with open(dst, "rb") as f:
                frames.append((t, f.read()))
        except (RenderError, OSError):
            continue
    return frames


def extract_audio_16k(path: str, dst: str) -> str:
    run([_bin("ffmpeg"), "-v", "error", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000", dst], 300)
    return dst


def _filter_path(p: str) -> str:
    # escape for use inside an ffmpeg filter argument
    return p.replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def _video_chain(src: Dict[str, Any], out_w: int, out_h: int, fmt: str) -> str:
    sw, sh = src["width"], src["height"]
    polish = []
    if max(sw, sh) < 1500:  # low-res phone/WhatsApp clip being upscaled: clean noise then sharpen
        polish = ["hqdn3d=1.5:1.5:3:3"]
    sharpen = "unsharp=5:5:0.5:5:5:0.0" if max(sw, sh) < 1500 else "unsharp=3:3:0.25:3:3:0.0"
    grade = "eq=contrast=1.04:saturation=1.07:gamma=1.02"
    src_ar, out_ar = sw / max(1, sh), out_w / max(1, out_h)
    if fmt == "vertical" and abs(src_ar - out_ar) > 0.12:
        # different shape (e.g. landscape into 9:16): blurred fill behind the full frame
        fg_w = out_w
        fg_h = int(round(out_w / src_ar)) // 2 * 2
        if fg_h > out_h:
            fg_h = out_h
            fg_w = int(round(out_h * src_ar)) // 2 * 2
        return (f"[0:v]{','.join(polish + ['fps=30', 'split=2'])}[a][b];"
                f"[a]scale={out_w}:{out_h}:force_original_aspect_ratio=increase,crop={out_w}:{out_h},"
                f"boxblur=24:3,eq=brightness=-0.08:saturation=1.1[bg];"
                f"[b]scale={fg_w}:{fg_h}:flags=lanczos,{sharpen},{grade}[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2")
    return (f"[0:v]{','.join(polish + ['fps=30'])},scale={out_w}:{out_h}:force_original_aspect_ratio=increase:"
            f"flags=lanczos,crop={out_w}:{out_h},{sharpen},{grade}")


def _audio_chain(mode: str, has_orig: bool, has_vo: bool) -> Tuple[str, str]:
    """Returns (filtergraph, output label). Input 0 = video file, input 1 = voiceover wav (if any)."""
    if mode in ("ai_mix", "ai_replace") and has_vo:
        vo = "[1:a]aresample=48000,highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,asplit=2[vo][sc]"
        if mode == "ai_mix" and has_orig:
            return (vo + ";[0:a]aresample=48000,highpass=f=100,volume=0.35[bg];"
                    "[bg][sc]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350[duck];"
                    "[vo][duck]amix=inputs=2:normalize=0:duration=longest[mix]", "[mix]")
        return vo + ";[sc]anullsink;[vo]anull[mix]", "[mix]"
    if has_orig:
        return "[0:a]aresample=48000,highpass=f=80[mix]", "[mix]"
    return "anullsrc=r=48000:cl=stereo[mix]", "[mix]"


def _loudnorm_measure(inputs: List[str], graph: str, label: str, duration: float) -> Optional[Dict[str, str]]:
    cmd = [_bin("ffmpeg"), "-hide_banner", "-nostats", "-y"]
    for i in inputs:
        cmd += ["-i", i]
    cmd += ["-filter_complex", graph + f";{label}loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json[o]",
            "-map", "[o]", "-t", f"{duration:.3f}", "-f", "null", "-"]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr.decode(errors="ignore"), re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        float(d["input_i"])
        if d["input_i"] in ("-inf", "inf"):
            return None
        return d
    except (ValueError, KeyError):
        return None


def render(*, src_path: str, src: Dict[str, Any], out_path: str, ass_path: Optional[str], vo_path: Optional[str],
           mode: str, fmt: str, duration: float, progress: Optional[Callable[[float], None]] = None) -> Dict[str, Any]:
    out_w, out_h = output_size(src["width"], src["height"], fmt)
    has_vo = bool(vo_path and os.path.exists(vo_path))
    inputs = [src_path] + ([vo_path] if has_vo else [])
    a_graph, a_label = _audio_chain(mode, src["has_audio"], has_vo)

    m = _loudnorm_measure(inputs, a_graph, a_label, duration)
    if m:
        ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
              f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    else:
        ln = "anull"
    v_graph = _video_chain(src, out_w, out_h, fmt)
    if ass_path:
        v_graph += f",ass='{_filter_path(ass_path)}':fontsdir='{_filter_path(FONTS_DIR)}'"
    v_graph += ",format=yuv420p[v]"
    graph = f"{v_graph};{a_graph};{a_label}{ln},aresample=48000[a]"

    cmd = [_bin("ffmpeg"), "-hide_banner", "-nostats", "-y"]
    for i in inputs:
        cmd += ["-i", i]
    cmd += ["-filter_complex", graph, "-map", "[v]", "-map", "[a]", "-t", f"{duration:.3f}",
            "-c:v", "libx264", "-preset", X264_PRESET, "-crf", X264_CRF, "-profile:v", "high",
            "-threads", FFMPEG_THREADS, "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", "-progress", "pipe:1", out_path]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    err_tail: List[str] = []
    import threading

    def _drain():
        for line in proc.stderr:  # type: ignore[union-attr]
            err_tail.append(line)
            del err_tail[:-8]

    t = threading.Thread(target=_drain, daemon=True)
    t.start()
    for line in proc.stdout:  # type: ignore[union-attr]
        if line.startswith("out_time_us=") and progress and duration > 0:
            try:
                progress(min(1.0, int(line.split("=", 1)[1]) / 1e6 / duration))
            except ValueError:
                pass
    proc.wait(timeout=3600)
    t.join(timeout=5)
    if proc.returncode != 0 or not os.path.exists(out_path):
        raise RenderError("Render failed: " + " | ".join(x.strip() for x in err_tail[-4:]))
    return {"width": out_w, "height": out_h, "loudness_measured": bool(m)}


def measure_loudness(path: str) -> Dict[str, Optional[float]]:
    r = subprocess.run([_bin("ffmpeg"), "-hide_banner", "-nostats", "-i", path, "-af", "ebur128=peak=true",
                        "-f", "null", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    txt = r.stderr.decode(errors="ignore")
    summ = txt[txt.rfind("Summary:"):] if "Summary:" in txt else txt
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", summ)
    p = re.search(r"Peak:\s+(-?[\d.]+) dBFS", summ)
    return {"lufs": float(i.group(1)) if i else None, "true_peak": float(p.group(1)) if p else None}
