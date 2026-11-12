import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("EDITOR_WORK_DIR", tempfile.mkdtemp(prefix="ed_test_"))

from starlette.testclient import TestClient

from backend.main import app
from backend import routes_editor
from backend.services.video_editor import captions, options, pipeline, planner

ORIGIN = {"Origin": "https://ovd.winplaybox.in"}


def _form(**kw):
    base = {"language": "hi", "mode": "ai_mix", "caption_style": "pop", "voice": "hm_omega",
            "caption_script": "roman", "brief": "test", "channel": "Dhrusa Vlogs"}
    base.update(kw)
    return base


class TestCaptions(unittest.TestCase):
    def setUp(self):
        self.words = captions.words_from_lines([
            {"caption": "Raat ke andhere mein, ek haadsa ho gaya.", "start": 0.3, "end": 3.0},
            {"caption": "Helmet pehniye.", "start": 3.3, "end": 4.5},
        ])

    def test_words_cover_lines_in_order(self):
        self.assertEqual(len(self.words), 10)
        self.assertAlmostEqual(self.words[0]["s"], 0.3)
        self.assertAlmostEqual(self.words[7]["e"], 3.0, places=2)
        self.assertTrue(all(a["s"] <= b["s"] for a, b in zip(self.words, self.words[1:])))
        self.assertTrue(self.words[3]["brk"])  # "mein," ends a phrase

    def test_every_style_renders_events(self):
        for st in ["pop", "single", "box", "karaoke", "minimal"]:
            ass = captions.build_ass(words=self.words, style=st, width=1080, height=1920, font="Inter Black",
                                     accent="#FFE500", duration=5)
            self.assertIn("PlayResY: 1920", ass)
            self.assertGreater(ass.count("Dialogue:"), 1, st)
        none = captions.build_ass(words=self.words, style="none", width=1080, height=1920, font="Inter Black",
                                  duration=5)
        self.assertNotIn("Dialogue:", none)

    def test_chunks_never_cross_phrase_break(self):
        chs = captions.chunk(captions.mark_breaks(self.words), 3)
        for ch in chs:
            self.assertFalse(any(w["brk"] for w in ch[:-1]))

    def test_text_is_escaped_and_colors_converted(self):
        self.assertEqual(captions.esc("a{\\b}c"), "abc")
        self.assertEqual(captions.ass_color("#FFE500"), "&H0000E5FF")
        self.assertEqual(captions.ass_color("bad"), "&H00FFFFFF")

    def test_hook_and_end_card(self):
        ass = captions.build_ass(words=[], style="none", width=1080, height=1920, font="Inter Black",
                                 hook={"title": "raat ka haadsa", "subtitle": ""},
                                 end_card={"title": "follow", "subtitle": "now"}, duration=30)
        self.assertIn("RAAT KA HAADSA", ass)
        self.assertIn("FOLLOW", ass)

    def test_srt(self):
        srt = captions.srt_from_words(self.words)
        self.assertTrue(srt.startswith("1\n00:00:00,300 --> "))


class TestPlanner(unittest.TestCase):
    def test_validate_script_repairs_order_and_bounds(self):
        out = planner.validate_script({"lines": [
            {"start": 5, "tts": "b", "caption": "B"},
            {"start": 2, "tts": "c"},
            {"start": "x", "tts": ""},
            {"start": 99, "tts": "d", "caption": "D"},
        ], "hook": {"title": "x" * 99}}, duration=20, need_lines=True)
        starts = [l["start"] for l in out["lines"]]
        self.assertEqual(starts, sorted(starts))
        self.assertLessEqual(starts[-1], 19.0)
        self.assertEqual(out["lines"][1]["caption"], "c")
        self.assertEqual(len(out["hook"]["title"]), 40)

    def test_validate_script_requires_lines_for_ai_modes(self):
        with self.assertRaises(planner.PlanError):
            planner.validate_script({"lines": []}, 10, need_lines=True)
        self.assertEqual(planner.validate_script({}, 10, need_lines=False)["lines"], [])

    def test_tags_trimmed_and_deduped(self):
        tags = ",".join(f"tag number {i}" for i in range(80)) + ",Tag Number 1"
        out = planner.validate_metadata({"tags": tags, "hashtags": ["shorts", "#viral", "#viral"]}, [])
        self.assertLessEqual(len(out["tags"]), planner.TAGS_MAX)
        self.assertEqual(out["hashtags"], ["#shorts", "#viral"])

    def test_links_extracted_and_enforced(self):
        brief = "all links value is https://bit.ly/m/DhrusaVlogs. Disclaimer too"
        links = planner.extract_links(brief)
        self.assertEqual(links, ["https://bit.ly/m/DhrusaVlogs"])
        out = planner.validate_metadata({"description": "Hello"}, links)
        self.assertIn("https://bit.ly/m/DhrusaVlogs", out["description"])


class TestOptions(unittest.TestCase):
    def test_every_language_has_a_voice(self):
        for lang in options.LANGUAGES:
            self.assertTrue(options.voices_for(lang["id"]), lang["id"])

    def test_voice_language_check(self):
        self.assertTrue(options.voice_ok_for("hm_omega", "hi"))
        self.assertFalse(options.voice_ok_for("hm_omega", "ta"))
        self.assertTrue(options.voice_ok_for("af_heart", "en-in"))


class TestEditorRoutes(unittest.TestCase):
    def setUp(self):
        wd = patch.object(pipeline, "WORK_DIR", tempfile.mkdtemp(prefix="ed_test_"))
        wd.start()
        self.addCleanup(wd.stop)
        self.client = TestClient(app, headers=ORIGIN)
        self.ip = f"10.9.{os.getpid() % 250}.{id(self) % 250}"

    def _post(self, data=None, files=True, ip=None):
        f = {"file": ("clip.mp4", b"\x00" * 2048, "video/mp4")} if files else None
        headers = {"X-Forwarded-For": ip or self.ip}
        return self.client.post("/api/editor/jobs", data=data or _form(), files=f, headers=headers)

    def test_options(self):
        r = self.client.get("/api/editor/options")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertTrue(body["voices"])
        self.assertEqual(body["quota"]["limit"], routes_editor.DAILY_LIMIT)

    def test_requires_site_origin(self):
        r = TestClient(app).get("/api/editor/options")
        self.assertEqual(r.status_code, 403)

    def test_validation_errors(self):
        self.assertEqual(self._post(files=False).status_code, 400)
        self.assertEqual(self._post(_form(language="xx")).status_code, 400)
        self.assertEqual(self._post(_form(voice="ta-IN-PallaviNeural")).status_code, 400)
        r = self.client.post("/api/editor/jobs", json={"a": 1})
        self.assertEqual(r.status_code, 400)

    @patch.object(routes_editor.pipeline, "start")
    def test_daily_limit_per_ip_and_refund(self, start):
        with patch.dict(os.environ, {"WPB_TRUST_PROXY": "1"}), patch("backend.security.zero_trust.TRUST_PROXY", True):
            ip = "203.0.113.77"
            r1 = self._post(ip=ip)
            self.assertEqual(r1.status_code, 202, r1.text)
            job1 = r1.json()["job"]
            # one active job at a time per client
            self.assertEqual(self._post(ip=ip).status_code, 409)
            j = pipeline.load_job(job1["id"])
            pipeline._update(j, status="done")
            r2 = self._post(ip=ip)
            self.assertEqual(r2.status_code, 202)
            self.assertEqual(r2.json()["quota"]["remaining"], 0)
            pipeline._update(pipeline.load_job(r2.json()["job"]["id"]), status="done")
            r3 = self._post(ip=ip)
            self.assertEqual(r3.status_code, 429)
            self.assertEqual(r3.json()["error"]["code"], "DailyLimitReached")
            # another IP is unaffected
            self.assertEqual(self._post(ip="203.0.113.78").status_code, 202)
            # a failed job gives the credit back
            on_finish = start.call_args_list[1].args[2]
            import asyncio
            asyncio.run(on_finish({"status": "failed"}))
            self.assertEqual(self._post(ip=ip).status_code, 202)

    def test_health(self):
        r = self.client.get("/api/editor/health")
        self.assertEqual(r.status_code, 200)
        self.assertIn("ffmpeg", r.json())
        self.assertIn("Inter-Black.otf", r.json()["fonts"])

    def test_warmup_needs_admin(self):
        self.assertEqual(self.client.post("/api/editor/warmup").status_code, 401)

    def test_job_status_and_files_404(self):
        self.assertEqual(self.client.get("/api/editor/jobs/not-a-uuid").status_code, 404)
        r = TestClient(app).get("/api/editor/jobs/00000000-0000-0000-0000-000000000000/file/video")
        self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
