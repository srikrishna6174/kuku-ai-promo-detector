import os
import glob
import json
import csv
import argparse
from typing import List, Dict, Any, Optional
from src.parser import parse_screenplay_file, format_time
from src.detector import find_promos_for_episode, PromoCandidate, generate_curated_multi_segment_promos
from src.ranker import rank_promos
from src.quality_checker import run_season_quality_audit
from src.llm_refiner import refine_with_llm
from src.export_utils import generate_ffmpeg_commands, generate_edl_markers

def run_season_detection(data_folder: str = "I Married a Broken Soldier. He was a Duke",
                         output_dir: str = "outputs",
                         top_k_per_ep: int = 2,
                         single_episode: Optional[int] = None,
                         provider: Optional[str] = None):
    """Processes screenplay episodes, extracts promos, ranks them, and writes outputs."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Locate files
    if os.path.isfile(data_folder):
        files = [data_folder]
    else:
        files = sorted(glob.glob(os.path.join(data_folder, "*.txt")))
        
    if not files:
        print(f"[!] No screenplay files found in: {data_folder}")
        return
        
    if single_episode is not None:
        files = [f for f in files if f"episode-{single_episode:03d}" in os.path.basename(f) or f"Episode {single_episode}" in os.path.basename(f)]
        if not files:
            print(f"[!] Episode {single_episode} not found in {data_folder}")
            return

    print(f"[*] Found {len(files)} episode file(s) to process.")
    print(f"[*] Scanning for high-converting 20s-60s promo moments (top_k={top_k_per_ep})...")

    all_promos: List[PromoCandidate] = []
    episodes_map = {}
    
    for idx, filepath in enumerate(files, 1):
        ep = parse_screenplay_file(filepath)
        episodes_map[ep.ep_number] = ep
        promos = find_promos_for_episode(ep, min_duration=20.0, max_duration=60.0, top_k=top_k_per_ep)
        all_promos.extend(promos)
        print(f"    Episode {ep.ep_number:02d}: found {len(promos)} promo candidates.")

    print(f"\n[*] Total candidates discovered: {len(all_promos)}")
    
    # Generate multi-segment promos
    stitched_promos = generate_curated_multi_segment_promos(episodes_map)
    print(f"[*] Generated {len(stitched_promos)} multi-segment viral trailer edits.")

    # Rank promos
    print(f"[*] Running strategic ranking (Acquisition vs Retargeting)...")
    ranked_promos = rank_promos(all_promos)

    # Optional LLM refinement for top 10 promos
    print(f"[*] Refining top candidate summaries (provider: {provider or 'auto'})...")
    for p in ranked_promos[:10]:
        refine_with_llm(p, provider=provider)

    # Quality and Failure mode audit
    print(f"[*] Performing quality audit and failure mode detection...")
    audit_report = run_season_quality_audit(ranked_promos)

    promos_dir = os.path.join(output_dir, "promos")
    individual_dir = os.path.join(promos_dir, "individual_promo_txt")
    intercut_dir = os.path.join(promos_dir, "intercut_trailers")
    audit_dir = os.path.join(output_dir, "quality_audit")
    editor_dir = os.path.join(output_dir, "editor_exports")
    for d in (output_dir, promos_dir, individual_dir, intercut_dir, audit_dir, editor_dir):
        os.makedirs(d, exist_ok=True)

    # 1. Export Master JSON
    json_path = os.path.join(promos_dir, "promos_master.json")
    promos_dict_list = [
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
    ]
    
    json_data = {
        "show_title": "I Married a Broken Soldier. He was a Duke",
        "total_episodes_processed": len(files),
        "total_promos_extracted": len(ranked_promos),
        "promos": promos_dict_list,
        "multi_segment_stitched_promos": stitched_promos
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)
    print(f"[+] Saved Master JSON -> {json_path}")

    # 2. Export Ranked CSV
    csv_path = os.path.join(promos_dir, "promos_ranked.csv")
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

    # 2b. Export Plain-Text Promo Report & Individual Cut Sheets
    from src.input_manager import build_promos_txt_report, format_single_promo_txt, format_stitched_promo_txt
    bundle_view = {
        "title": "I Married a Broken Soldier. He was a Duke",
        "episode_count": len(files),
        "detection_label": provider or "Rule-Based",
        "created_at": "CLI Run",
        "promos": promos_dict_list,
        "stitched_promos": stitched_promos,
    }
    report_path = os.path.join(promos_dir, "promos_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(build_promos_txt_report(bundle_view))
    for pd_item in promos_dict_list:
        r_num = int(pd_item.get("rank", 0))
        e_num = int(pd_item.get("episode", 1))
        with open(os.path.join(individual_dir, f"promo_rank{r_num:03d}_ep{e_num:02d}.txt"), "w", encoding="utf-8") as f:
            f.write(format_single_promo_txt(pd_item, show_title=bundle_view["title"]))
    for s_idx, s_item in enumerate(stitched_promos, 1):
        with open(os.path.join(intercut_dir, f"intercut_{s_idx:02d}.txt"), "w", encoding="utf-8") as f:
            f.write(format_stitched_promo_txt(s_item, idx=s_idx, show_title=bundle_view["title"]))
    print(f"[+] Saved Promo .txt Reports -> {promos_dir}")

    # 3. Export Quality Audit & Failure Report
    audit_path = os.path.join(audit_dir, "quality_audit_and_failures.json")
    with open(audit_path, 'w', encoding='utf-8') as f:
        json.dump(audit_report, f, indent=2)
    print(f"[+] Saved Quality & Failure Audit -> {audit_path}")

    # 4. Export FFmpeg Slicing Scripts
    ffmpeg_script = generate_ffmpeg_commands(promos_dict_list)
    sh_path = os.path.join(editor_dir, "cut_promos.sh")
    bat_path = os.path.join(editor_dir, "cut_promos.bat")
    with open(sh_path, 'w', encoding='utf-8') as f:
        f.write(ffmpeg_script)
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(ffmpeg_script)
    print(f"[+] Saved FFmpeg Cut Scripts -> {sh_path} and {bat_path}")

    # 5. Export Premiere Pro / DaVinci Resolve Markers
    edl_path = os.path.join(editor_dir, "premiere_markers.csv")
    generate_edl_markers(promos_dict_list, edl_path)
    print(f"[+] Saved Video Editor Markers -> {edl_path}")

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
    parser = argparse.ArgumentParser(description="Kuku AI Promo Finder CLI")
    parser.add_argument("--input", "-i", type=str, default="I Married a Broken Soldier. He was a Duke",
                        help="Path to episode file or folder containing screenplays")
    parser.add_argument("--output-dir", "-o", type=str, default="outputs",
                        help="Output directory for generated JSON, CSV, and scripts")
    parser.add_argument("--top-k", "-k", type=int, default=2,
                        help="Top K promo candidates per episode")
    parser.add_argument("--episode", "-e", type=int, default=None,
                        help="Filter and run on a single episode number (e.g. --episode 3)")
    parser.add_argument("--provider", "-p", type=str, default=None,
                        choices=["gemini", "openai", "auto", "offline"],
                        help="LLM model provider for semantic refinement")

    args = parser.parse_args()
    run_season_detection(
        data_folder=args.input,
        output_dir=args.output_dir,
        top_k_per_ep=args.top_k,
        single_episode=args.episode,
        provider=args.provider
    )
