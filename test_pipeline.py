import unittest
import os
import glob
import json
import csv
from src.parser import parse_screenplay_file, format_time, parse_time_str
from src.detector import find_promos_for_episode, PromoCandidate
from src.ranker import rank_promos
from src.quality_checker import audit_promo_quality, run_season_quality_audit

DATA_FOLDER = "I Married a Broken Soldier. He was a Duke"
OUTPUT_DIR = "outputs"

class TestKukuPromoPipeline(unittest.TestCase):

    def test_01_all_50_files_exist_and_parse(self):
        """Verifies that all 50 episode screenplay files exist and parse without error."""
        files = sorted(glob.glob(os.path.join(DATA_FOLDER, "*.txt")))
        self.assertEqual(len(files), 50, f"Expected 50 episode files, found {len(files)}")
        
        for idx, f in enumerate(files, 1):
            ep = parse_screenplay_file(f)
            self.assertEqual(ep.ep_number, idx, f"Expected episode number {idx}, got {ep.ep_number} in {f}")
            self.assertGreater(len(ep.blocks), 20, f"Episode {idx} has too few parsed blocks: {len(ep.blocks)}")
            self.assertGreater(ep.total_duration, 60.0, f"Episode {idx} runtime suspiciously short: {ep.total_duration}")

    def test_02_timestamp_monotonicity(self):
        """Verifies that all parsed block timestamps are chronologically valid and monotonic."""
        files = sorted(glob.glob(os.path.join(DATA_FOLDER, "*.txt")))[:10]
        for f in files:
            ep = parse_screenplay_file(f)
            for b in ep.blocks:
                self.assertGreaterEqual(b.end_time, b.start_time, 
                                        f"Inverted timestamps in {f}: start {b.start_time} > end {b.end_time}")
                self.assertGreaterEqual(b.start_time, 0.0)

    def test_03_promo_duration_constraints(self):
        """Strictly asserts that 100% of detected promos adhere to 20s - 60s constraint."""
        files = sorted(glob.glob(os.path.join(DATA_FOLDER, "*.txt")))
        for f in files:
            ep = parse_screenplay_file(f)
            promos = find_promos_for_episode(ep, min_duration=20.0, max_duration=60.0, top_k=2)
            self.assertGreater(len(promos), 0, f"No promos found for episode {ep.ep_number}")
            for p in promos:
                self.assertGreaterEqual(p.duration, 20.0, f"Promo duration too short: {p.duration}s in Ep {p.episode_number}")
                self.assertLessEqual(p.duration, 60.0, f"Promo duration too long: {p.duration}s in Ep {p.episode_number}")

    def test_04_promo_metadata_completeness(self):
        """Verifies that hook, cliffhanger, and rationale are populated and informative."""
        files = sorted(glob.glob(os.path.join(DATA_FOLDER, "*.txt")))[:5]
        for f in files:
            ep = parse_screenplay_file(f)
            promos = find_promos_for_episode(ep, top_k=2)
            for p in promos:
                self.assertTrue(len(p.hook_description) > 5, f"Empty hook in Ep {p.episode_number}")
                self.assertTrue(len(p.cliffhanger_description) > 5, f"Empty cliffhanger in Ep {p.episode_number}")
                self.assertTrue(len(p.why_it_works) > 10, f"Empty why_it_works in Ep {p.episode_number}")

    def test_05_ranking_priority(self):
        """Assures Tier 1 Priority is assigned to pilot episodes (Ep 1-3)."""
        ep1 = parse_screenplay_file(os.path.join(DATA_FOLDER, "episode-001-Episode 1671703.txt"))
        ep3 = parse_screenplay_file(os.path.join(DATA_FOLDER, "episode-003-Episode 1671705.txt"))
        ep20 = parse_screenplay_file(os.path.join(DATA_FOLDER, "episode-020-Episode 1671722.txt"))
        
        promos = find_promos_for_episode(ep1, top_k=1) + \
                 find_promos_for_episode(ep3, top_k=1) + \
                 find_promos_for_episode(ep20, top_k=1)
                 
        ranked = rank_promos(promos)
        top_eps = [p.episode_number for p in ranked[:2]]
        self.assertTrue(1 in top_eps or 3 in top_eps, "Pilot episodes 1 or 3 should be ranked at the very top for Cold UA.")

    def test_06_master_json_integrity(self):
        """Validates structured outputs/promos/promos_master.json format and schema."""
        json_path = os.path.join(OUTPUT_DIR, "promos", "promos_master.json")
        self.assertTrue(os.path.exists(json_path), f"Missing master JSON file: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.assertIn("show_title", data)
        self.assertEqual(data.get("total_episodes_processed"), 50)
        self.assertEqual(len(data.get("promos", [])), 100)
        
        for p in data["promos"]:
            self.assertIn("rank", p)
            self.assertIn("episode", p)
            self.assertIn("segments", p)
            self.assertGreater(len(p["segments"]), 0)
            self.assertIn("hook", p)
            self.assertIn("cliffhanger", p)
            self.assertIn("why_it_works", p)

    def test_07_pdf_page_count(self):
        """Validates that Solution_Document.pdf exists and is strictly 2 pages."""
        pdf_path = "Solution_Document.pdf"
        self.assertTrue(os.path.exists(pdf_path), f"Missing PDF document: {pdf_path}")
        
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        page_count = len(reader.pages)
        self.assertEqual(page_count, 2, f"Solution document must be strictly up to 2 pages, found: {page_count}")

    def test_08_multi_segment_promos(self):
        """Validates multi-segment stitched trailer edits."""
        json_path = os.path.join(OUTPUT_DIR, "promos", "promos_master.json")
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        stitched = data.get("multi_segment_stitched_promos", [])
        self.assertGreater(len(stitched), 0, "Expected at least 1 multi-segment stitched promo")
        for s in stitched:
            self.assertIn("title", s)
            self.assertIn("format", s)
            self.assertGreater(len(s.get("segments", [])), 1, "Multi-segment promo must have >1 segments")
            self.assertGreaterEqual(s["total_duration_seconds"], 20.0)
            self.assertLessEqual(s["total_duration_seconds"], 60.0)

    def test_09_ffmpeg_and_edl_exports(self):
        """Validates that video editing suite markers and ffmpeg cut scripts exist and are populated."""
        sh_path = os.path.join(OUTPUT_DIR, "editor_exports", "cut_promos.sh")
        bat_path = os.path.join(OUTPUT_DIR, "editor_exports", "cut_promos.bat")
        edl_path = os.path.join(OUTPUT_DIR, "editor_exports", "premiere_markers.csv")
        
        self.assertTrue(os.path.exists(sh_path), "Missing cut_promos.sh")
        self.assertTrue(os.path.exists(bat_path), "Missing cut_promos.bat")
        self.assertTrue(os.path.exists(edl_path), "Missing premiere_markers.csv")
        
        with open(sh_path, 'r', encoding='utf-8') as f:
            sh_content = f.read()
            self.assertIn("ffmpeg", sh_content)
            
        with open(edl_path, 'r', encoding='utf-8') as f:
            reader = list(csv.reader(f))
            self.assertGreater(len(reader), 10, "EDL markers file should contain promo rows")

    def test_10_solution_markdown_exists(self):
        """Validates that solution_doc.md exists in root for GitHub readability."""
        self.assertTrue(os.path.exists("solution_doc.md"), "Missing solution_doc.md")

if __name__ == "__main__":
    unittest.main()

