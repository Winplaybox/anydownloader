"""
AI Agent Universe (1,000 domain agents + 200 script agents + 100 domains) for GravityClaw.

The workbook rows are combinatorial archetypes (domain x function) with identical generic text,
so the expertise comes from the playbooks below:
  FUNCTION_PLAYBOOKS - how each of the 10 agent functions works (method, deliverable, checks)
  FAMILY_PLAYBOOKS   - craft rules + guardrails for each of the 22 script families
  RISK_GROUPS        - extra guardrails for regulated domain groups
Each agent resolves to a `profile` that is injected into the GravityClaw system prompt.
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "agent_universe_v3.json")

FUNCTION_PLAYBOOKS: Dict[str, Dict[str, Any]] = {
    "Researcher": {
        "mission": "find, compare and synthesize trustworthy information",
        "method": ["Clarify the research question and scope", "List the evidence needed and where it comes from",
                   "Compare sources, note agreement and conflicts", "Synthesize findings with confidence levels",
                   "Flag gaps and what still needs verification"],
        "deliverable": "research brief with key findings, evidence table, confidence and open questions",
        "checks": ["Every claim traceable to a source or marked as assumption", "Conflicting evidence surfaced", "No invented statistics"],
        "target": "llm_task", "output_type": "Research brief",
    },
    "Writer / Generator": {
        "mission": "create a polished, audience-fit deliverable",
        "method": ["Lock audience, goal and format", "Outline before drafting", "Draft with a strong opening and clear structure",
                   "Edit for clarity, tone and length", "Add CTA / next step"],
        "deliverable": "finished draft in the requested format",
        "checks": ["Matches tone and audience", "Clear structure with headings/sections", "Within length budget"],
        "target": "llm_task", "output_type": "Article",
    },
    "Analyst": {
        "mission": "turn inputs into insights and decisions",
        "method": ["Define the question and success metric", "Profile the data/inputs", "Find patterns, outliers and drivers",
                   "Quantify impact where possible", "Recommend actions ranked by impact and effort"],
        "deliverable": "analysis report: summary, findings, evidence, recommendations",
        "checks": ["Numbers reproducible", "Correlation vs causation stated", "Assumptions explicit"],
        "target": "llm_task", "output_type": "Report",
    },
    "Planner": {
        "mission": "convert goals into an executable plan",
        "method": ["Restate goal and constraints", "Break into phases and milestones", "Sequence tasks with dependencies and owners",
                   "Estimate time/effort and risks", "Define checkpoints and success criteria"],
        "deliverable": "plan/roadmap with phases, tasks, owners, timeline, risks",
        "checks": ["Every task has an owner and done-criteria", "Dependencies ordered", "Risks have mitigations"],
        "target": "llm_task", "output_type": "Plan/roadmap",
    },
    "Quality Reviewer": {
        "mission": "audit work against standards and catch defects",
        "method": ["State the rubric/standard", "Review section by section", "Classify issues by severity",
                   "Give concrete fixes for each issue", "Summarize pass/fail with score"],
        "deliverable": "review report: severity-ranked issues with fixes and a score",
        "checks": ["Issues are specific and actionable", "Severity justified", "No vague praise"],
        "target": "llm_task", "output_type": "Checklist",
    },
    "Verifier": {
        "mission": "fact-check claims and validate correctness",
        "method": ["Extract each verifiable claim", "Check against reliable references", "Mark verified / unverified / false",
                   "Explain corrections with evidence", "List what needs a human expert"],
        "deliverable": "claim-by-claim verification table with verdicts and corrections",
        "checks": ["Each claim has a verdict", "Uncertainty not hidden", "Corrections cite evidence"],
        "target": "llm_task", "output_type": "Checklist",
    },
    "Tutor / Explainer": {
        "mission": "teach a concept so the learner truly understands",
        "method": ["Assess the learner's level", "Explain with a simple analogy first", "Build up step by step with examples",
                   "Check understanding with questions", "Summarize and give practice"],
        "deliverable": "lesson with explanation, examples, quick quiz and recap",
        "checks": ["Jargon defined", "Examples relatable to audience", "Ends with practice / quiz"],
        "target": "llm_task", "output_type": "Lesson plan",
    },
    "Optimizer": {
        "mission": "improve an existing process, asset or system against a metric",
        "method": ["Baseline the current state and metric", "Identify bottlenecks / weak points", "Propose ranked improvements",
                   "Estimate gain and cost of each", "Define how to measure the result"],
        "deliverable": "optimization plan: baseline, ranked changes, expected impact, measurement",
        "checks": ["Metric defined", "Changes ranked by ROI", "Before/after measurable"],
        "target": "llm_task", "output_type": "Report",
    },
    "Knowledge Curator": {
        "mission": "organize knowledge into a reusable, findable structure",
        "method": ["Collect and deduplicate sources", "Define taxonomy and tags", "Write concise entries with links",
                   "Mark freshness and owners", "Define update cadence"],
        "deliverable": "structured knowledge base / FAQ with taxonomy",
        "checks": ["No duplicates", "Consistent taxonomy", "Each entry has source and date"],
        "target": "llm_task", "output_type": "Structured JSON",
    },
    "Workflow Automator": {
        "mission": "design reliable automations that remove manual work",
        "method": ["Map the manual process and trigger", "Define each step's input/output", "Choose tools/integrations",
                   "Add error handling, retries and approvals", "Define monitoring and rollback"],
        "deliverable": "workflow definition: trigger, nodes, data mapping, error handling, schedule",
        "checks": ["Idempotent steps", "Human approval for consequential actions", "Failure alerts defined"],
        "target": "n8n_workflow", "output_type": "Workflow definition",
    },
}

_SHORT_VIDEO = "short_video_script"
FAMILY_PLAYBOOKS: Dict[str, Dict[str, Any]] = {
    "Video & Film": {"rules": ["Hook within 3 seconds", "One idea per scene", "Visual direction for every line", "Retention re-hooks"], "target": _SHORT_VIDEO},
    "Social Media": {"rules": ["Pattern-interrupt opening", "Under 60s spoken", "On-screen text for silent viewers", "Single CTA"], "target": _SHORT_VIDEO},
    "Storytelling": {"rules": ["Clear protagonist and want", "Rising tension", "Vivid sensory detail", "Satisfying ending or twist"], "target": "llm_task"},
    "Horror": {"rules": ["Slow-burn dread over gore", "Grounded relatable setting", "Sound cues and silence", "Unresolved last beat", "No real-person defamation or real tragedy exploitation"], "target": _SHORT_VIDEO},
    "Mythology & Culture": {"rules": ["Respectful, scripture-faithful framing", "Name sources (e.g. Valmiki Ramayana, Vyasa Mahabharata) and note regional variants", "No mockery of deities or communities", "Moral takeaway"], "target": _SHORT_VIDEO},
    "Religious & Cultural": {"rules": ["Reverent tone", "Accurate rituals and terms", "Avoid sectarian claims", "Inclusive framing"], "target": "voice_over"},
    "Education": {"rules": ["Learning objective first", "Analogy then detail", "Accurate facts; flag uncertainty", "Recap at end"], "target": _SHORT_VIDEO},
    "Science & Nature": {"rules": ["Scientifically accurate", "Wonder-driven narration", "Units and scale made relatable", "Cite consensus"], "target": "youtube_long"},
    "Children": {"rules": ["Age-appropriate words", "Positive values", "No scary or unsafe content", "Repetition and rhythm"], "target": "llm_task"},
    "Comedy": {"rules": ["Setup-punchline rhythm", "Punch up, not down", "No hate or stereotypes", "Callback ending"], "target": _SHORT_VIDEO},
    "Documentary": {"rules": ["Evidence-based", "Neutral narrator voice", "Archival/B-roll notes", "Chapters with timestamps"], "target": "youtube_long"},
    "News": {"rules": ["Facts first, attributed", "Neutral language", "Date and place stated", "No speculation as fact"], "target": _SHORT_VIDEO},
    "Marketing": {"rules": ["Customer pain first", "Benefit over feature", "Proof element", "One clear CTA", "No false claims"], "target": "ad_copy"},
    "Sales": {"rules": ["Problem-agitate-solve", "Objection handling", "Social proof", "Clear offer and CTA"], "target": _SHORT_VIDEO},
    "Business": {"rules": ["Professional tone", "Clear structure", "Key message per section", "Action items"], "target": "llm_task"},
    "Personal Development": {"rules": ["Relatable story", "Actionable steps", "Encouraging not preachy", "No medical/financial guarantees"], "target": _SHORT_VIDEO},
    "Technology": {"rules": ["Accurate steps and versions", "Show, then explain", "Prerequisites listed", "Troubleshooting tip"], "target": "youtube_long"},
    "Travel & Food": {"rules": ["Sensory descriptions", "Practical tips (cost, timing, how to reach)", "Cultural respect", "Shot ideas"], "target": _SHORT_VIDEO},
    "Podcast & Audio": {"rules": ["Conversational voice", "Segment structure with timestamps", "Host transitions", "Show notes"], "target": "voice_over"},
    "Gaming": {"rules": ["Character voice consistency", "Branching options where useful", "Lore consistency", "Player motivation"], "target": "llm_task"},
    "Adaptation": {"rules": ["Preserve source meaning", "Re-structure for new format", "Cut to essentials", "Credit the source"], "target": _SHORT_VIDEO},
    "Script Quality": {"rules": ["Score against a rubric", "Line-level fixes", "Severity-ranked issues", "Rewrite the weakest part"], "target": "llm_task"},
}

RISK_GROUPS = {
    "Healthcare": "Educational information only - no diagnosis or dosing; advise consulting a qualified professional; cite reputable sources.",
    "Wellness": "No medical claims or guarantees; encourage professional advice for health concerns.",
    "Finance": "Not financial advice; no guaranteed returns; disclose risks; follow local regulations.",
    "Legal": "General information, not legal advice; jurisdiction matters; recommend a licensed lawyer.",
    "Public Services": "Use official sources; state dates; avoid political bias.",
}

OUTPUT_TYPE_TARGETS = {
    "Video script": "youtube_long", "Short-form script": _SHORT_VIDEO, "Screenplay": "llm_task", "Podcast script": "voice_over",
    "Dialogue": "llm_task", "Article": "seo_blog", "Blog post": "seo_blog", "Social caption": "social_caption", "Ad copy": "ad_copy",
    "Email/message": "email", "Report": "llm_task", "Research brief": "llm_task", "Storyboard": _SHORT_VIDEO,
    "Image prompt": "flux", "Video prompt": "kling", "Audio/narration": "voice_over", "Code": "coding_agent",
    "Test suite": "coding_agent", "Data table": "llm_task", "Dashboard specification": "ui_screen", "Checklist": "llm_task",
    "Plan/roadmap": "llm_task", "Presentation outline": "llm_task", "Lesson plan": "llm_task", "Quiz/assessment": "llm_task",
    "Translation": "llm_task", "Summary": "llm_task", "Structured JSON": "llm_task", "Workflow definition": "n8n_workflow",
    "Agent specification": "llm_system",
}

_LONG_HINT = re.compile(r"long-form|documentary|episode|lesson|chapter|podcast episode|tutorial|walkthrough", re.I)
_TOKEN = re.compile(r"[a-z0-9]+")


class AgentUniverse:
    def __init__(self, path: str = DATA) -> None:
        with open(path, encoding="utf-8") as f:
            self.data: Dict[str, Any] = json.load(f)
        self.by_id: Dict[str, Dict[str, Any]] = {}
        for a in self.data["agents"] + self.data["script_agents"]:
            self.by_id[a["id"].upper()] = a
        self.domains = {d["id"]: d for d in self.data["domains"]}
        self.output_types = {o["name"]: o for o in self.data["output_types"]}
        self.workflows = {w["name"]: w for w in self.data["workflows"]}
        self._index: List[Tuple[Dict[str, Any], set]] = [
            (a, set(_TOKEN.findall(" ".join(str(a.get(k, "")) for k in ("name", "domain", "group", "function", "family", "purpose", "deliverable")).lower())))
            for a in self.data["agents"] + self.data["script_agents"]
        ]

    # ------------------------------------------------------------------ lookup
    def get(self, agent_id: Optional[str]) -> Optional[Dict[str, Any]]:
        return self.by_id.get(str(agent_id or "").strip().upper())

    def default_target(self, a: Dict[str, Any], output_type: Optional[str] = None, requirement: str = "") -> str:
        if output_type and output_type in OUTPUT_TYPE_TARGETS:
            return OUTPUT_TYPE_TARGETS[output_type]
        if a["kind"] == "script":
            fam = FAMILY_PLAYBOOKS.get(a.get("family", ""), {})
            name = a.get("name", "")
            if re.search(r"advertisement|commercial|ad\b", name, re.I):
                return "ad_copy"
            if re.search(r"reel|shorts|tiktok|short-video", name, re.I):
                return _SHORT_VIDEO
            if _LONG_HINT.search(name) and fam.get("target") == _SHORT_VIDEO:
                return "youtube_long"
            return fam.get("target", "llm_task")
        if re.search(r"\b(agent|assistant|chatbot|bot|gpt|copilot)\b", requirement, re.I):
            return "llm_system"
        fn = FUNCTION_PLAYBOOKS.get(a.get("function", ""), {})
        if a.get("group") == "Technology" and a.get("function") in ("Writer / Generator", "Optimizer", "Verifier", "Quality Reviewer"):
            return "coding_agent"
        return fn.get("target", "llm_task")

    def profile(self, a: Dict[str, Any]) -> Dict[str, Any]:
        shared = self.data["shared"][a["kind"]]
        if a["kind"] == "agent":
            fn = FUNCTION_PLAYBOOKS.get(a["function"], FUNCTION_PLAYBOOKS["Writer / Generator"])
            dom = self.domains.get(a.get("domain_id", ""), {})
            guard = RISK_GROUPS.get(a.get("group", ""))
            return {
                "id": a["id"], "kind": "agent", "name": a["name"], "role": f"{a['domain']} {a['function']}",
                "domain": a["domain"], "domain_scope": dom.get("scope", ""), "group": a.get("group"),
                "function": a["function"], "purpose": a["purpose"], "mission": fn["mission"],
                "method": fn["method"], "deliverable": fn["deliverable"], "checks": fn["checks"],
                "guardrails": ([guard] if guard else []) + [f"Human review: {shared['human_review']}"],
                "default_output_type": fn["output_type"],
            }
        fam = FAMILY_PLAYBOOKS.get(a.get("family", ""), {"rules": []})
        return {
            "id": a["id"], "kind": "script", "name": a["name"], "role": a["name"], "family": a.get("family"),
            "deliverable": a.get("deliverable"), "mission": f"write a production-ready {a.get('deliverable', 'script').lower()}",
            "method": [s.strip() for s in shared["workflow"].split("→")],
            "craft_rules": fam["rules"], "checks": [c.strip() for c in shared["checks"].split(";")],
            "customize": [c.strip() for c in shared["customization"].split(";")],
            "guardrails": [r for r in fam["rules"] if re.search(r"\bno\b|respect|accurate|neutral|faithful|safe", r, re.I)],
            "default_output_type": "Short-form script" if fam.get("target") == _SHORT_VIDEO else "Video script",
        }

    def system_block(self, prof: Dict[str, Any], *, workflow: Optional[str] = None, output_type: Optional[str] = None,
                     platform: Optional[str] = None, audience: Optional[str] = None) -> str:
        lines = [f"EXPERT AGENT PROFILE ({prof['id']}): You are acting as the '{prof['name']}' - your mission is to {prof['mission']}."]
        if prof.get("domain_scope"):
            lines.append(f"Domain: {prof['domain']} ({prof['domain_scope']}).")
        if prof.get("family"):
            lines.append(f"Script family: {prof['family']}.")
        lines.append("Method the prompt must make the target AI follow: " + " -> ".join(prof["method"]) + ".")
        if prof.get("deliverable"):
            lines.append(f"Expected deliverable: {prof['deliverable']}.")
        if prof.get("craft_rules"):
            lines.append("Craft rules: " + "; ".join(prof["craft_rules"]) + ".")
        lines.append("Quality checks to bake in: " + "; ".join(prof["checks"]) + ".")
        if prof.get("guardrails"):
            lines.append("Guardrails: " + " ".join(prof["guardrails"]))
        if workflow and workflow in self.workflows:
            lines.append(f"Workflow pattern: {workflow} - {self.workflows[workflow]['description']}.")
        if output_type and output_type in self.output_types:
            lines.append(f"Output type: {output_type} - {self.output_types[output_type]['definition']}.")
        if platform:
            lines.append(f"Platform: {platform}.")
        if audience:
            lines.append(f"Audience: {audience}.")
        lines.append("Embed this expertise INSIDE the generated prompt (role, method, checks) so any AI tool that receives it performs like this expert.")
        return "\n".join(lines)

    # ------------------------------------------------------------------ search
    def search(self, q: str = "", *, kind: Optional[str] = None, domain: Optional[str] = None, family: Optional[str] = None,
               function: Optional[str] = None, group: Optional[str] = None, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        terms = set(_TOKEN.findall((q or "").lower()))
        out: List[Tuple[float, Dict[str, Any]]] = []
        for a, toks in self._index:
            if kind and a["kind"] != kind:
                continue
            if domain and a.get("domain") != domain and a.get("domain_id") != domain:
                continue
            if family and a.get("family") != family:
                continue
            if function and a.get("function") != function:
                continue
            if group and a.get("group") != group:
                continue
            if terms:
                hits = sum(1 for t in terms if t in toks or any(x.startswith(t) for x in toks))
                if not hits:
                    continue
                score = hits / len(terms) + (0.5 if (q or "").lower() in a["name"].lower() else 0) + (0.1 if a["kind"] == "script" else 0)
            else:
                score = 0.0
            out.append((score, a))
        out.sort(key=lambda x: (-x[0], x[1]["id"]))
        total = len(out)
        page = [self.summary(a) for _, a in out[offset: offset + limit]]
        return {"total": total, "offset": offset, "limit": limit, "items": page}

    def summary(self, a: Dict[str, Any]) -> Dict[str, Any]:
        s = {"id": a["id"], "kind": a["kind"], "name": a["name"], "default_target": self.default_target(a)}
        if a["kind"] == "agent":
            s.update(domain=a["domain"], group=a["group"], function=a["function"], purpose=a["purpose"])
        else:
            s.update(family=a["family"], deliverable=a["deliverable"])
        return s

    def facets(self) -> Dict[str, Any]:
        d = self.data
        return {
            "version": d["version"], "counts": d["counts"],
            "functions": sorted(FUNCTION_PLAYBOOKS), "script_families": sorted(FAMILY_PLAYBOOKS),
            "domain_groups": sorted({x["group"] for x in d["domains"]}),
            "domains": [{"id": x["id"], "name": x["name"], "group": x["group"]} for x in d["domains"]],
            "output_types": [x["name"] for x in d["output_types"]],
            "workflows": [x["name"] for x in d["workflows"]],
            "platforms": d["config"].get("platforms", []), "audiences": d["config"].get("audiences", []),
            "tones": d["config"].get("tones", []), "languages": d["config"].get("languages", []),
        }


@lru_cache(maxsize=1)
def universe() -> AgentUniverse:
    return AgentUniverse()
