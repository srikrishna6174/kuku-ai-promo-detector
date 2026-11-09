import os
import re
from typing import List, Dict, Any, Optional

def parse_time_str(ts: str) -> float:
    """Converts MM:SS.SS or HH:MM:SS.SS to total seconds."""
    parts = ts.strip().split(':')
    if len(parts) == 2:
        minutes, seconds = parts
        return float(minutes) * 60 + float(seconds)
    elif len(parts) == 3:
        hours, minutes, seconds = parts
        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    return float(ts)

def format_time(seconds: float) -> str:
    """Converts total seconds back to MM:SS.SS."""
    minutes = int(seconds // 60)
    rem_seconds = seconds % 60
    return f"{minutes:02d}:{rem_seconds:05.2f}"

class ScriptBlock:
    def __init__(self, block_type: str, speaker: Optional[str], tone: Optional[str], 
                 start_time: float, end_time: float, content: str, raw_text: str = ""):
        self.block_type = block_type  # 'CAMERA', 'ACTION', 'SOUND FX', 'MUSIC', 'DIALOGUE'
        self.speaker = speaker
        self.tone = tone
        self.start_time = start_time
        self.end_time = end_time
        self.content = content.strip().strip('"')
        self.raw_text = raw_text

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)

    @property
    def start_formatted(self) -> str:
        return format_time(self.start_time)

    @property
    def end_formatted(self) -> str:
        return format_time(self.end_time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_type": self.block_type,
            "speaker": self.speaker,
            "tone": self.tone,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "start_formatted": format_time(self.start_time),
            "end_formatted": format_time(self.end_time),
            "duration": round(self.duration, 2),
            "content": self.content
        }

class Episode:
    def __init__(self, ep_number: int, title: str, logline: str, continuity: str, 
                 blocks: List[ScriptBlock], raw_path: str):
        self.ep_number = ep_number
        self.title = title
        self.logline = logline
        self.continuity = continuity
        self.blocks = blocks
        self.raw_path = raw_path
        self.total_duration = blocks[-1].end_time if blocks else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_number": self.ep_number,
            "title": self.title,
            "logline": self.logline,
            "continuity": self.continuity,
            "total_duration": round(self.total_duration, 2),
            "total_duration_formatted": format_time(self.total_duration),
            "block_count": len(self.blocks),
            "dialogue_count": len([b for b in self.blocks if b.block_type == 'DIALOGUE'])
        }

def parse_screenplay_file(filepath: str) -> Episode:
    """Parses an episode screenplay text file into a structured Episode object."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Normalize line endings
    content = content.replace('\r\n', '\n')

    # Extract metadata
    ep_num_match = re.search(r'EPISODE NUMBER:\s*Episode\s*(\d+)', content, re.IGNORECASE)
    ep_num = int(ep_num_match.group(1)) if ep_num_match else 0
    
    logline_match = re.search(r'EPISODE LOGLINE:\s*(.*?)(?=\n[A-Z\s]+:|\n---|\Z)', content, re.DOTALL)
    logline = logline_match.group(1).strip() if logline_match else ""

    cont_match = re.search(r'CONTINUITY NOTES:\s*(.*?)(?=\n--- SCRIPT START|\Z)', content, re.DOTALL)
    continuity = cont_match.group(1).strip() if cont_match else ""

    # Locate script body
    script_start = content.find("--- SCRIPT START ---")
    script_end = content.find("--- SCRIPT END ---")
    if script_start != -1:
        body = content[script_start + len("--- SCRIPT START ---"):script_end if script_end != -1 else len(content)]
    else:
        body = content

    # Split into blocks starting with **TAG**: \nStart: (MM:SS.SS) | End: (MM:SS.SS)
    block_pattern = re.compile(
        r'\*\*([^*]+)\*\*\s*\n'
        r'Start:\s*\((\d+:\d+\.\d+)\)\s*\|\s*End:\s*\((\d+:\d+\.\d+)\)\s*\n'
        r'(.*?)(?=(?:\n\*\*[^*]+\*\*\s*\nStart:|\nSCENE\s+\d+|\n--- SCRIPT END|\Z))',
        re.DOTALL
    )

    blocks: List[ScriptBlock] = []
    for match in block_pattern.finditer(body):
        raw_header = match.group(1).strip().rstrip(':')
        start_ts = parse_time_str(match.group(2))
        end_ts = parse_time_str(match.group(3))
        text_content = match.group(4).strip()

        # Determine block type
        known_cues = ['CAMERA', 'ACTION', 'SOUND FX', 'MUSIC']
        is_cue = False
        for cue in known_cues:
            if raw_header.upper().startswith(cue):
                blocks.append(ScriptBlock(cue, None, None, start_ts, end_ts, text_content, match.group(0)))
                is_cue = True
                break

        if not is_cue:
            # It is dialogue: format like "CHARACTER_NAME (Tone, Notes)"
            speaker = raw_header
            tone = None
            if '(' in raw_header and ')' in raw_header:
                parts = raw_header.split('(', 1)
                speaker = parts[0].strip()
                tone = parts[1].rstrip(')').strip()
            
            blocks.append(ScriptBlock('DIALOGUE', speaker, tone, start_ts, end_ts, text_content, match.group(0)))

    # Sort blocks chronologically
    blocks.sort(key=lambda b: (b.start_time, b.end_time))
    
    return Episode(
        ep_number=ep_num,
        title=f"Episode {ep_num}",
        logline=logline,
        continuity=continuity,
        blocks=blocks,
        raw_path=filepath
    )
