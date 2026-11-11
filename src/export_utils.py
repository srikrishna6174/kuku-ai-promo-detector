import os
import csv
from typing import List, Dict, Any

def generate_ffmpeg_commands(promos: List[Dict[str, Any]], 
                             video_dir: str = "videos", 
                             output_dir: str = "promo_clips") -> str:
    """
    Generates bash and batch script commands to automatically slice video files
    using ffmpeg based on the discovered promo timestamps.
    """
    commands = [
        "# Automated FFmpeg Clip Extraction Script for Kuku Microdramas",
        "# Usage: bash cut_promos.sh (Linux/Mac) or run cut_promos.bat (Windows)",
        f"mkdir -p {output_dir}",
        ""
    ]
    
    for p in promos:
        rank = p.get("rank", 0)
        ep = p.get("episode", 1)
        seg = p.get("segments", [{}])[0]
        start_ts = seg.get("start_time", "00:00.00")
        end_ts = seg.get("end_time", "00:30.00")
        dur = p.get("total_duration_seconds", 30.0)
        
        # Convert MM:SS.SS to HH:MM:SS.SS
        start_ffmpeg = f"00:{start_ts}"
        end_ffmpeg = f"00:{end_ts}"
        
        input_file = f"{video_dir}/episode_{ep:03d}.mp4"
        output_file = f"{output_dir}/promo_rank{rank:02d}_ep{ep:02d}_{int(dur)}s.mp4"
        
        # Fast stream copy command
        cmd = f"ffmpeg -y -ss {start_ffmpeg} -to {end_ffmpeg} -i \"{input_file}\" -c copy \"{output_file}\""
        commands.append(f"# Rank #{rank} (Ep {ep} | {dur}s): {p.get('hook', '')[:50]}")
        commands.append(cmd)
        commands.append("")
        
    return "\n".join(commands)

def generate_edl_markers(promos: List[Dict[str, Any]], output_filepath: str):
    """
    Generates a standard CMX 3600 Edit Decision List (EDL) / CSV marker file
    for direct import into Adobe Premiere Pro, DaVinci Resolve, or Final Cut Pro.
    """
    with open(output_filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "Marker Name", "Description", "In Timecode", "Out Timecode", 
            "Duration (s)", "Rank", "Marketing Tier", "Clip Name"
        ])
        for p in promos:
            seg = p.get("segments", [{}])[0]
            writer.writerow([
                f"Promo_Rank_{p.get('rank', 0):02d}_Ep{p.get('episode', 0):02d}",
                f"Hook: {p.get('hook', '')} | Cliffhanger: {p.get('cliffhanger', '')}",
                f"00:{seg.get('start_time', '00:00.00')}:00",
                f"00:{seg.get('end_time', '00:30.00')}:00",
                p.get("total_duration_seconds", 0),
                p.get("rank", 0),
                p.get("marketing_tier", ""),
                f"Episode_{p.get('episode', 0):02d}.mp4"
            ])

