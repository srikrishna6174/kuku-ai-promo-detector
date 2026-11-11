import io
import os
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from src.detector import (
    build_manual_promo_candidate,
    find_promos_for_episode,
    generate_curated_multi_segment_promos,
)
from src.input_manager import (
    add_manual_cut_to_bundle,
    add_rule_based_promos_to_bundle,
    build_export_artifacts,
    build_promos_txt_zip,
    delete_saved_bundle,
    enhance_bundle_with_ai,
    list_saved_inputs,
    load_saved_bundle,
    parse_uploaded_files_as_separate_inputs,
    parse_uploaded_sources,
    pin_manual_cut_any_bundle,
    process_episodes_into_bundle,
    save_bundle_to_disk,
)
from src.llm_refiner import LLMProviderConfig, detect_promos_with_llms, get_backend_provider_status, load_backend_env
from src.parser import parse_screenplay_text
from src.quality_checker import infer_main_protagonists, run_season_quality_audit
from src.ranker import rank_promos


SAMPLE_CORPORATE_SCRIPT = """EPISODE NUMBER: Episode 1
EPISODE LOGLINE: CFO confronts CEO at midnight board meeting.

--- SCRIPT START ---

**CEO VANCE (Cold, Threatening):**
Start: (00:00.00) | End: (00:04.50)
"You called an emergency vote at midnight, Maya. Why?"

**MAYA (Calm, Defiant):**
Start: (00:04.80) | End: (00:09.20)
"Fourteen million dollars vanished from the pension fund. Your signature is on every wire."

**SOUND FX:**
Start: (00:09.20) | End: (00:11.00)
Electronic door bolts lock with a sharp metallic slam.

**CEO VANCE (Furious):**
Start: (00:11.30) | End: (00:16.00)
"Nobody leaves this floor if they threaten my board seat!"

**MAYA (Uncompromising):**
Start: (00:16.30) | End: (00:21.50)
"Too late. The federal prosecutor is watching this livestream right now."

**CEO VANCE (Panicked, Whispering):**
Start: (00:21.80) | End: (00:25.60)
"Who gave you my private encryption key...?"

**SOUND FX:**
Start: (00:25.60) | End: (00:27.50)
Low bass drone swells, then cut to black.

--- SCRIPT END ---
"""

SAMPLE_SRT = """1
00:00:00,000 --> 00:00:04,500
DETECTIVE KIM: Why did you erase the security footage at 2 AM?

2
00:00:04,800 --> 00:00:09,500
DR. PARK: You think I erased it to protect myself?

3
00:00:09,800 --> 00:00:15,200
DETECTIVE KIM: The server logs prove your badge opened the vault!

4
00:00:15,500 --> 00:00:21,000
DR. PARK: Look closely at the timestamp. I was in surgery with the mayor.

5
00:00:21,300 --> 00:00:26,400
DETECTIVE KIM: Wait... if you were in surgery, then who is standing behind you right now?!
"""

SAMPLE_PLAIN = """CAPTAIN NOVA: Oxygen reserves in Sector 4 just dropped to twelve percent!
ENGINEER KAI: That's impossible, I sealed the bulkhead myself ten minutes ago!
CAPTAIN NOVA: Then someone overrode the airlock from the bridge.
ENGINEER KAI: There are only three officers with bridge clearance...
[ACTION: Red emergency klaxons flash as footsteps echo down the corridor.]
CAPTAIN NOVA: Wait. Where is Commander Thorne?
ENGINEER KAI: Don't open that door—he's not alone!
"""


class FakeUpload:
    def __init__(self, name: str, data: bytes):
        self.name = name
        self._data = data

    def getvalue(self) -> bytes:
        return self._data


class TestUniversalAndMultiLLM(unittest.TestCase):
    def test_01_multi_format_parsing(self):
        ep_kuku = parse_screenplay_text(SAMPLE_CORPORATE_SCRIPT, source_name="corp.txt")
        self.assertEqual(ep_kuku.source_format, "kuku_screenplay")
        self.assertFalse(ep_kuku.timestamps_estimated)
        self.assertGreaterEqual(len(ep_kuku.blocks), 6)

        ep_srt = parse_screenplay_text(SAMPLE_SRT, source_name="mystery.srt")
        self.assertEqual(ep_srt.source_format, "srt_subtitles")
        self.assertEqual(len(ep_srt.blocks), 5)
        self.assertEqual(ep_srt.blocks[0].speaker, "DETECTIVE KIM")

        ep_plain = parse_screenplay_text(SAMPLE_PLAIN, source_name="scifi.txt")
        self.assertEqual(ep_plain.source_format, "plain_script_estimated")
        self.assertTrue(ep_plain.timestamps_estimated)
        self.assertGreater(ep_plain.total_duration, 20.0)

    def test_02_zip_upload_and_universal_detection(self):
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr("ep_02.srt", SAMPLE_SRT)
            zf.writestr("ep_01.txt", SAMPLE_CORPORATE_SCRIPT)

        eps, title = parse_uploaded_sources(uploaded_files=[FakeUpload("my_show_season.zip", buf.getvalue())])
        self.assertEqual(len(eps), 2)

        bundle = process_episodes_into_bundle(
            episodes=eps,
            title="Test Multi-Genre Season",
            detection_mode="manual",
            min_duration=20.0,
            max_duration=60.0,
            top_k_per_ep=2,
        )
        self.assertGreaterEqual(len(bundle["promos"]), 2)
        # Ensure Duke show stitches and Duke protagonists are NOT injected into non-Duke shows
        for s in bundle["stitched_promos"]:
            self.assertNotIn("Juliana", s["title"])
            self.assertNotIn("Altar Betrayal", s["title"])
        inferred = bundle["audit_report"]["inferred_protagonists"]
        self.assertNotIn("JULIANA", inferred)
        self.assertTrue(any(c in inferred for c in ("CEO VANCE", "MAYA", "DETECTIVE KIM", "DR. PARK")))

    def test_03_custom_cliffhanger_keywords_and_manual_cut(self):
        ep = parse_screenplay_text(SAMPLE_CORPORATE_SCRIPT)
        promos = find_promos_for_episode(
            ep,
            min_duration=15.0,
            max_duration=60.0,
            top_k=1,
            custom_hook_keywords=["pension fund"],
            custom_cliffhanger_keywords=["encryption key"],
            custom_only=True,
        )
        self.assertEqual(len(promos), 1)

        pinned = build_manual_promo_candidate(ep, start_time=4.8, end_time=25.6, cliffhanger_note="Custom cut!")
        self.assertIsNotNone(pinned)
        self.assertEqual(pinned.detection_method, "Manual Cut")
        self.assertEqual(pinned.cliffhanger_description, "Custom cut!")

    def test_04_multi_llm_failover_and_judge(self):
        ep = parse_screenplay_text(SAMPLE_CORPORATE_SCRIPT)
        manual_cands = find_promos_for_episode(ep, min_duration=20.0, max_duration=60.0, top_k=1)

        p1 = LLMProviderConfig(name="gemini", api_key="fake-1", model="gemini-2.5-flash")
        p2 = LLMProviderConfig(name="openai", api_key="fake-2", model="gpt-4o-mini")
        p3 = LLMProviderConfig(name="groq", api_key="fake-3", model="llama-3.3-70b-versatile")

        def mock_call(cfg, prompt, timeout=30):
            # Simulate Gemini going down completely (network/429 error)
            if cfg.name == "gemini":
                raise RuntimeError("HTTP 429: Gemini quota exceeded")

            # Judge prompt
            if "LLM-as-a-Judge" in prompt:
                # Also simulate OpenAI failing as Judge so Groq takes over Judge failover!
                if cfg.name == "openai":
                    raise RuntimeError("HTTP 503: OpenAI temporarily unavailable")
                return {
                    "judgments": [
                        {
                            "candidate_id": 0,
                            "hook_strength": 9.4,
                            "cliffhanger_pull": 9.6,
                            "standalone_clarity": 9.0,
                            "pacing_quality": 9.2,
                            "judge_score": 93.5,
                            "judge_verdict": "Strong boardroom betrayal hook and sharp encryption-key cliffhanger.",
                        }
                    ]
                }

            # Candidate proposal prompt (OpenAI + Groq succeed while Gemini fails)
            return {
                "candidates": [
                    {
                        "start_idx": 0,
                        "end_idx": 5,
                        "hook_score": 8.8,
                        "cliffhanger_score": 9.3,
                        "coherence_score": 8.7,
                        "hook_summary": "CEO challenges Maya at midnight before she drops an embezzlement bomb.",
                        "cliffhanger_summary": "Cuts as Vance whispers: 'Who gave you my private encryption key...?'",
                        "why_it_works": "Immediate financial betrayal stakes and an unanswered traitor question.",
                    }
                ]
            }

        with patch("src.llm_refiner.call_provider_json", side_effect=mock_call):
            selected, tel = detect_promos_with_llms(
                episode=ep,
                providers=[p1, p2, p3],
                min_duration=20.0,
                max_duration=60.0,
                top_k=2,
                manual_candidates=manual_cands,
                use_judge=True,
                judge_provider_name="openai",
                detection_mode="both",
                run_all_active_llms=True,
            )

        self.assertGreaterEqual(len(selected), 1)
        self.assertTrue(tel["failover_triggered"])
        self.assertIn("Google Gemini", [f["provider"] for f in tel["provider_failures"]])
        self.assertIn("OpenAI", tel["providers_succeeded"])
        self.assertIn("Groq", tel["providers_succeeded"])
        # Primary judge OpenAI failed, so Groq seamlessly acted as Judge
        self.assertTrue(tel["judge_used"])
        self.assertIn("Groq", tel["judge_provider"])
        self.assertIsNotNone(selected[0].judge_verdict)
        self.assertEqual(selected[0].judge_verdict["judge_score"], 93.5)

    def test_05_saved_input_library_persistence_and_exports(self):
        ep = parse_screenplay_text(SAMPLE_SRT, source_name="detective.srt")
        bundle = process_episodes_into_bundle(
            episodes=[ep],
            title="Detective Mystery Pilot",
            detection_mode="manual",
            min_duration=15.0,
            max_duration=60.0,
            top_k_per_ep=2,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            save_bundle_to_disk(bundle, base_dir=tmpdir)
            listed = list_saved_inputs(base_dir=tmpdir)
            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0]["title"], "Detective Mystery Pilot")

            loaded = load_saved_bundle(bundle["id"], base_dir=tmpdir)
            self.assertIsNotNone(loaded)
            self.assertEqual(len(loaded["promos"]), len(bundle["promos"]))
            self.assertEqual(len(loaded["episodes"]), 1)

            ok, _ = add_manual_cut_to_bundle(
                loaded,
                episode_number=1,
                start_time=0.0,
                end_time=21.0,
                cliffhanger_note="Extra pin",
                base_dir=tmpdir,
            )
            self.assertTrue(ok)
            self.assertEqual(len(loaded["promos"]), len(bundle["promos"]) + 1)

            artifacts = build_export_artifacts(loaded)
            self.assertIn("Detective Mystery Pilot", artifacts["json"])
            self.assertIn("ffmpeg", artifacts["ffmpeg"])
            self.assertIn("Marker Name", artifacts["edl"])
            self.assertIn("Source Episode(s):", artifacts["txt"])
            self.assertIn("Intercut", artifacts["txt"])
            self.assertIn("SCRIPT EXCERPT IN CUT WINDOW:", artifacts["txt"])

            txt_zip_bytes = build_promos_txt_zip(loaded)
            with zipfile.ZipFile(io.BytesIO(txt_zip_bytes), "r") as zf:
                names = zf.namelist()
                self.assertIn("00_ALL_PROMOS_SUMMARY.txt", names)
                self.assertTrue(any(n.startswith("promo_rank01_") and n.endswith(".txt") for n in names))

            self.assertTrue(delete_saved_bundle(bundle["id"], base_dir=tmpdir))
            self.assertEqual(len(list_saved_inputs(base_dir=tmpdir)), 0)

    def test_06_multiple_txt_files_separate_and_combined(self):
        f1 = FakeUpload("ep1_corp.txt", SAMPLE_CORPORATE_SCRIPT.encode("utf-8"))
        f2 = FakeUpload("ep2_scifi.txt", SAMPLE_PLAIN.encode("utf-8"))

        # Combined mode
        combined_eps, _ = parse_uploaded_sources(uploaded_files=[f1, f2])
        self.assertEqual(len(combined_eps), 2)

        # Separate mode
        separate_batches = parse_uploaded_files_as_separate_inputs([f1, f2])
        self.assertEqual(len(separate_batches), 2)
        self.assertEqual(separate_batches[0][1], "Ep1 Corp")
        self.assertEqual(separate_batches[1][1], "Ep2 Scifi")

    def test_07_backend_env_loader(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = os.path.join(tmpdir, ".env")
            with open(env_file, "w", encoding="utf-8") as f:
                f.write("TEST_KUKU_SAMPLE_VAR=configured_ok\n")
            os.environ.pop("TEST_KUKU_SAMPLE_VAR", None)
            load_backend_env(env_file)
            self.assertEqual(os.environ.pop("TEST_KUKU_SAMPLE_VAR", None), "configured_ok")

    def test_08_only_gemini_and_openai_exposed_in_status(self):
        statuses = get_backend_provider_status()
        self.assertEqual([s["name"] for s in statuses], ["gemini", "openai"])
        self.assertEqual(statuses[0]["model"], "gemini-3.8-flash")
        self.assertEqual(statuses[1]["model"], "gpt-4o-mini")

    def test_09_enhance_offline_bundle_with_ai(self):
        ep = parse_screenplay_text(SAMPLE_CORPORATE_SCRIPT)
        bundle = process_episodes_into_bundle(
            episodes=[ep],
            title="Offline First Project",
            detection_mode="manual",
            min_duration=15.0,
            max_duration=60.0,
            top_k_per_ep=1,
        )
        self.assertEqual(bundle["detection_mode"], "manual")

        p_gem = LLMProviderConfig(name="gemini", api_key="fake-gem")

        def mock_call(cfg, prompt, timeout=30):
            if "LLM-as-a-Judge" in prompt:
                return {
                    "judgments": [
                        {
                            "candidate_id": 0,
                            "hook_strength": 9.1,
                            "cliffhanger_pull": 9.3,
                            "standalone_clarity": 8.9,
                            "pacing_quality": 9.0,
                            "judge_score": 91.5,
                            "judge_verdict": "Sharp corporate standoff.",
                        }
                    ]
                }
            return {
                "candidates": [
                    {
                        "start_idx": 0,
                        "end_idx": 5,
                        "hook_score": 8.7,
                        "cliffhanger_score": 9.2,
                        "coherence_score": 8.8,
                        "hook_summary": "Boardroom midnight confrontation.",
                        "cliffhanger_summary": "Cuts on encryption key mystery.",
                        "why_it_works": "Instant tension and high stakes.",
                    }
                ]
            }

        with patch("src.llm_refiner.call_provider_json", side_effect=mock_call):
            updated, tel = enhance_bundle_with_ai(
                bundle=bundle,
                llm_providers=[p_gem],
                target_episodes=[1],
                action="merge",
                min_duration=15.0,
                max_duration=60.0,
                use_judge=True,
            )

        self.assertTrue(tel["judge_used"])
        self.assertIn("AI", updated["detection_label"])
        self.assertGreaterEqual(len(updated["promos"]), 1)
        self.assertIsNotNone(updated["promos"][0].get("judge_verdict"))

    def test_10_manual_cut_and_rule_based_on_ai_bundle(self):
        ep = parse_screenplay_text(SAMPLE_CORPORATE_SCRIPT)
        p_gem = LLMProviderConfig(name="gemini", api_key="fake-gem")

        def mock_ai(cfg, prompt, timeout=30):
            return {
                "candidates": [
                    {
                        "start_idx": 0,
                        "end_idx": 4,
                        "hook_score": 8.8,
                        "cliffhanger_score": 9.1,
                        "coherence_score": 8.9,
                        "hook_summary": "Emergency midnight vote opening.",
                        "cliffhanger_summary": "Freeze on missing wire proof.",
                        "why_it_works": "High stakes from second zero.",
                    }
                ]
            }

        with patch("src.llm_refiner.call_provider_json", side_effect=mock_ai):
            ai_bundle = process_episodes_into_bundle(
                episodes=[ep],
                title="AI First Project",
                detection_mode="llm",
                min_duration=15.0,
                max_duration=60.0,
                top_k_per_ep=1,
                llm_providers=[p_gem],
                use_judge=False,
            )

        self.assertEqual(len(ai_bundle["promos"]), 1)
        self.assertIn("LLM", ai_bundle["promos"][0]["detection_method"])

        with tempfile.TemporaryDirectory() as tmpdir:
            ok, _, mc_bundle = pin_manual_cut_any_bundle(
                ai_bundle,
                episode_number=1,
                start_time=0.0,
                end_time=21.0,
                cliffhanger_note="User manual pin after AI",
                base_dir=tmpdir,
            )
            self.assertTrue(ok)
            self.assertEqual(len(mc_bundle["promos"]), 2)
            self.assertTrue(any(p.get("detection_method") == "Manual Cut" for p in mc_bundle["promos"]))

            merged_bundle, added_cnt = add_rule_based_promos_to_bundle(
                mc_bundle,
                min_duration=15.0,
                max_duration=60.0,
                top_k_per_ep=1,
                base_dir=tmpdir,
            )
            self.assertGreaterEqual(added_cnt, 1)
            methods = [p.get("detection_method", "") for p in merged_bundle["promos"]]
            self.assertTrue(any("Manual Cut" in m for m in methods))
            self.assertTrue(any("LLM" in m for m in methods))
            self.assertTrue(any("Rule-Based" in m for m in methods))


if __name__ == "__main__":
    unittest.main()

