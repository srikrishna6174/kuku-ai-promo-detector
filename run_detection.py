import os
import glob
import json
import csv
from typing import List
from src.parser import parse_screenplay_file, format_time
from src.detector import find_promos_for_episode, PromoCandidate, generate_curated_multi_segment_promos
from src.ranker import rank_promos
from src.quality_checker import run_season_quality_audit
from src.llm_refiner import refine_with_llm

def run_season_detection(data_folder: str = "I Married a Broken Soldier. He was a Duke",
                         output_dir: str = "outputs",
                         top_k_per_ep: int = 2):
    """Processes all 50 screenplay episodes, extracts promos, ranks them, and writes outputs."""
    os.makedirs(output_dir, exist_ok=True)
    
    files = sorted(glob.glob(os.path.join(data_folder, "*.txt")))
    if not files:
        print(f"[!] No screenplay files found in: {data_folder}")
        return
        
    print(f"[*] Found {len(files)} episode files in '{data_folder}'")
    print(f"[*] Scanning for high-converting 20s-60s promo moments...")

    all_promos: List[PromoCandidate] = []
    episodes_map = {}
    
    for idx, filepath in enumerate(files, 1):
        ep = parse_screenplay_file(filepath)
        episodes_map[ep.ep_number] = ep
        promos = find_promos_for_episode(ep, min_duration=20.0, max_duration=60.0, top_k=top_k_per_ep)
        all_promos.extend(promos)
        print(f"    Episode {ep.ep_number:02d}: found {len(promos)} promo candidates.")

    print(f"\n[*] Total candidates discovered: {len(all_promos)}")
    print(f"[*] Generating curated multi-segment stitched promos...")
    stitched_promos = generate_curated_multi_segment_promos(episodes_map)
    print(f"    Generated {len(stitched_promos)} multi-segment viral trailer edits.")

    print(f"[*] Running strategic ranking (Acquisition vs Retargeting)...")
    ranked_promos = rank_promos(all_promos)

    # Optional LLM refinement for top 10 promos
    print(f"[*] Refining top candidate summaries...")
    for p in ranked_promos[:10]:
        refine_with_llm(p)

    # Quality and Failure mode audit
    print(f"[*] Performing quality audit and failure mode detection...")
    audit_report = run_season_quality_audit(ranked_promos)

    # 1. Export Master JSON
    json_path = os.path.join(output_dir, "promos_master.json")
    json_data = {
        "show_title": "I Married a Broken Soldier. He was a Duke",
        "total_episodes_processed": len(files),
        "total_promos_extracted": len(ranked_promos),
        "promos": [
            {
                "rank": p.rank,
                "episode": p.episode_number,
                "segments": [
                    {
                        "segment_index": 1,
                        "start_time": format_time(p.start_time),
                        "end_time": format_time(p.end_time),
                        "duration_seconds": p.duration
                    }
                ],
                "total_duration_seconds": p.duration,
                "marketing_tier": p.funnel_type,
                "total_score": p.total_score,
                "hook_score": p.hook_score,
                "cliffhanger_score": p.cliffhanger_score,
                "hook": p.hook_description,
                "cliffhanger": p.cliffhanger_description,
                "why_it_works": p.why_it_works,
                "script_excerpt": [
                    {
                        "start": b.start_formatted,
                        "end": b.end_formatted,
                        "type": b.block_type,
                        "speaker": b.speaker,
                        "tone": b.tone,
                        "content": b.content
                    }
                    for b in p.blocks
                ]
            }
            for p in ranked_promos
        ],
        "multi_segment_stitched_promos": stitched_promos
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    print(f"[+] Saved Master JSON -> {json_path}")

    # 2. Export Ranked CSV
    csv_path = os.path.join(output_dir, "promos_ranked.csv")
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Rank", "Episode", "Start Time", "End Time", "Duration (s)", 
            "Marketing Tier", "Score (0-100)", "Hook", "Cliffhanger", "Why It Works"
        ])
        for p in ranked_promos:
            writer.writerow([
                p.rank,
                p.episode_number,
                format_time(p.start_time),
                format_time(p.end_time),
                p.duration,
                p.funnel_type,
                p.total_score,
                p.hook_description,
                p.cliffhanger_description,
                p.why_it_works
            ])
    print(f"[+] Saved Ranked CSV -> {csv_path}")

    # 3. Export Quality Audit & Failure Report
    audit_path = os.path.join(output_dir, "quality_audit_and_failures.json")
    with open(audit_path, 'w', encoding='utf-8') as f:
        json.dump(audit_report, f, indent=2)
    print(f"[+] Saved Quality & Failure Audit -> {audit_path}")

    # Print Top 5 Summary
    print("\n" + "="*70)
    print("🏆 TOP 5 PROMOS TO POST FIRST (Highest Organic Acquisition Potential)")
    print("="*70)
    for p in ranked_promos[:5]:
        print(f"Rank #{p.rank} | Ep {p.episode_number} | {format_time(p.start_time)} -> {format_time(p.end_time)} ({p.duration}s) | Score: {p.total_score}")
        print(f"  Hook: {p.hook_description}")
        print(f"  Cliffhanger: {p.cliffhanger_description}")
        print(f"  Why: {p.why_it_works}\n")

if __name__ == "__main__":
    run_season_detection()

