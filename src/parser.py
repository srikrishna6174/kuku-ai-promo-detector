import os
import re
from typing import List, Dict, Any, Optional, Tuple


def parse_time_str(ts: str) -> float:
    """Converts SS.SS, MM:SS.SS, or HH:MM:SS.SS (including comma ms) to total seconds."""
    cleaned = ts.strip().replace(",", ".")
    parts = cleaned.split(":")
    if len(parts) == 2:
        minutes, seconds = parts
        return float(minutes) * 60 + float(seconds)
    elif len(parts) == 3:
        hours, minutes, seconds = parts
        return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    return float(cleaned)


def format_time(seconds: float) -> str:
    """Converts total seconds back to MM:SS.SS."""
    seconds = max(0.0, float(seconds))
    minutes = int(seconds // 60)
    rem_seconds = seconds % 60
    return f"{minutes:02d}:{rem_seconds:05.2f}"


class ScriptBlock:
    def __init__(
        self,
        block_type: str,
        speaker: Optional[str],
        tone: Optional[str],
        start_time: float,
        end_time: float,
        content: str,
        raw_text: str = "",
    ):
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
            "content": self.content,
        }


class Episode:
    def __init__(
        self,
        ep_number: int,
        title: str,
        logline: str,
        continuity: str,
        blocks: List[ScriptBlock],
        raw_path: str,
        source_format: str = "kuku_screenplay",
        timestamps_estimated: bool = False,
    ):
        self.ep_number = ep_number
        self.title = title
        self.logline = logline
        self.continuity = continuity
        self.blocks = blocks
        self.raw_path = raw_path
        self.source_format = source_format
        self.timestamps_estimated = timestamps_estimated
        self.total_duration = blocks[-1].end_time if blocks else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_number": self.ep_number,
            "title": self.title,
            "logline": self.logline,
            "continuity": self.continuity,
            "source_format": self.source_format,
            "timestamps_estimated": self.timestamps_estimated,
            "total_duration": round(self.total_duration, 2),
            "total_duration_formatted": format_time(self.total_duration),
            "block_count": len(self.blocks),
            "dialogue_count": len([b for b in self.blocks if b.block_type == "DIALOGUE"]),
        }


def _extract_speaker_and_tone(raw_header: str) -> Tuple[str, Optional[str]]:
    """Splits 'CHARACTER (Tone, Notes)' into ('CHARACTER', 'Tone, Notes')."""
    speaker = raw_header.strip().rstrip(":")
    tone = None
    if "(" in speaker and ")" in speaker:
        parts = speaker.split("(", 1)
        speaker = parts[0].strip()
        tone = parts[1].rsplit(")", 1)[0].strip()
    return speaker, tone


def _infer_episode_number(content: str, source_name: str, default_ep_number: Optional[int]) -> int:
    """Extracts episode number from header, filename, or falls back safely."""
    ep_num_match = re.search(r"EPISODE NUMBER:\s*(?:Episode|Ep\.?)\s*(\d+)", content, re.IGNORECASE)
    if ep_num_match:
        return int(ep_num_match.group(1))

    ep_header_alt = re.search(r"^\s*(?:Episode|EP)\s+(\d+)\b", content, re.IGNORECASE | re.MULTILINE)
    if ep_header_alt:
        return int(ep_header_alt.group(1))

    base = os.path.basename(source_name or "")
    file_match = re.search(r"(?:episode|ep)[-_ ]*(\d+)", base, re.IGNORECASE)
    if file_match:
        return int(file_match.group(1))

    num_only = re.match(r"^(\d+)(?:\.\w+)?$", base)
    if num_only:
        return int(num_only.group(1))

    return default_ep_number if default_ep_number is not None else 1


def _parse_kuku_blocks(body: str) -> List[ScriptBlock]:
    """Parses **TAG**\\nStart: (MM:SS.SS) | End: (MM:SS.SS) format."""
    block_pattern = re.compile(
        r"\*\*([^*]+)\*\*\s*\n"
        r"Start:\s*\((\d+(?::\d+)*(?:\.\d+)?)\)\s*\|\s*End:\s*\((\d+(?::\d+)*(?:\.\d+)?)\)\s*\n"
        r"(.*?)(?=(?:\n\*\*[^*]+\*\*\s*\nStart:|\nSCENE\s+\d+|\n--- SCRIPT END|\Z))",
        re.DOTALL,
    )
    known_cues = ["CAMERA", "ACTION", "SOUND FX", "MUSIC"]
    blocks: List[ScriptBlock] = []

    for match in block_pattern.finditer(body):
        raw_header = match.group(1).strip().rstrip(":")
        start_ts = parse_time_str(match.group(2))
        end_ts = parse_time_str(match.group(3))
        text_content = match.group(4).strip()

        is_cue = False
        for cue in known_cues:
            if raw_header.upper().startswith(cue):
                blocks.append(ScriptBlock(cue, None, None, start_ts, end_ts, text_content, match.group(0)))
                is_cue = True
                break

        if not is_cue:
            speaker, tone = _extract_speaker_and_tone(raw_header)
            blocks.append(ScriptBlock("DIALOGUE", speaker, tone, start_ts, end_ts, text_content, match.group(0)))

    return blocks


def _parse_srt_blocks(content: str) -> List[ScriptBlock]:
    """Parses standard SRT / VTT subtitle blocks."""
    srt_pattern = re.compile(
        r"(?:\d+\s*\n)?"
        r"(\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}|\d{1,2}:\d{2}[.,]\d{1,3})\s*-->\s*"
        r"(\d{1,2}:\d{2}:\d{2}[.,]\d{1,3}|\d{1,2}:\d{2}[.,]\d{1,3})[^\n]*\n"
        r"(.*?)(?=\n\s*\n|\Z)",
        re.DOTALL,
    )
    blocks: List[ScriptBlock] = []
    for m in srt_pattern.finditer(content):
        start_ts = parse_time_str(m.group(1))
        end_ts = parse_time_str(m.group(2))
        raw_line = " ".join(line.strip() for line in m.group(3).splitlines() if line.strip())
        if not raw_line:
            continue

        # Check for bracketed cues like [MUSIC] or [SFX: ...]
        cue_match = re.match(r"^\[(CAMERA|ACTION|SOUND FX|SFX|MUSIC)\s*:?\s*(.*)\]$", raw_line, re.IGNORECASE)
        if cue_match:
            btype = "SOUND FX" if cue_match.group(1).upper() == "SFX" else cue_match.group(1).upper()
            blocks.append(ScriptBlock(btype, None, None, start_ts, end_ts, cue_match.group(2) or raw_line, m.group(0)))
            continue

        # Check for SPEAKER: line
        spk_match = re.match(r"^([A-Z][A-Za-z0-9 .'\-()]{1,35}):\s+(.+)$", raw_line)
        if spk_match:
            speaker, tone = _extract_speaker_and_tone(spk_match.group(1))
            blocks.append(ScriptBlock("DIALOGUE", speaker, tone, start_ts, end_ts, spk_match.group(2), m.group(0)))
        else:
            blocks.append(ScriptBlock("DIALOGUE", "SPEAKER", None, start_ts, end_ts, raw_line, m.group(0)))

    return blocks


def _parse_inline_timestamp_blocks(content: str) -> List[ScriptBlock]:
    """Parses [MM:SS] SPEAKER: text, (MM:SS) SPEAKER: text, or MM:SS - MM:SS | SPEAKER: text."""
    line_pattern = re.compile(
        r"^\s*[\[\(]?(\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)[\]\)]?"
        r"(?:\s*[-–—>]+\s*[\[\(]?(\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)[\]\)]?)?"
        r"\s*(?:\|\s*)?(.+?)\s*$"
    )
    parsed_items: List[Tuple[float, Optional[float], str, str]] = []

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        m = line_pattern.match(stripped)
        if m:
            start_ts = parse_time_str(m.group(1))
            end_ts = parse_time_str(m.group(2)) if m.group(2) else None
            rest = m.group(3).strip()
            if rest:
                parsed_items.append((start_ts, end_ts, rest, stripped))

    if len(parsed_items) < 2:
        return []

    blocks: List[ScriptBlock] = []
    for idx, (start_ts, end_ts, rest, raw_line) in enumerate(parsed_items):
        if end_ts is None:
            word_est = max(1.8, len(rest.split()) / 2.4 + 0.5)
            if idx + 1 < len(parsed_items) and parsed_items[idx + 1][0] > start_ts:
                end_ts = min(parsed_items[idx + 1][0], start_ts + max(word_est, 4.0))
            else:
                end_ts = start_ts + word_est
        end_ts = max(end_ts, start_ts + 0.5)

        cue_match = re.match(r"^(CAMERA|ACTION|SOUND FX|SFX|MUSIC)\s*[:\-]\s*(.+)$", rest, re.IGNORECASE)
        if cue_match:
            btype = "SOUND FX" if cue_match.group(1).upper() == "SFX" else cue_match.group(1).upper()
            blocks.append(ScriptBlock(btype, None, None, start_ts, end_ts, cue_match.group(2), raw_line))
            continue

        spk_match = re.match(r"^([A-Za-z][A-Za-z0-9 .'\-()]{1,35}):\s+(.+)$", rest)
        if spk_match:
            speaker, tone = _extract_speaker_and_tone(spk_match.group(1))
            blocks.append(ScriptBlock("DIALOGUE", speaker, tone, start_ts, end_ts, spk_match.group(2), raw_line))
        else:
            blocks.append(ScriptBlock("DIALOGUE", "SPEAKER", None, start_ts, end_ts, rest, raw_line))

    return blocks


def _parse_plain_script_blocks(content: str) -> List[ScriptBlock]:
    """
    Fallback parser for un-timestamped screenplays, dialogue transcripts, or prose.
    Estimates realistic speaking/action durations (~2.4 words/sec + beat gap).
    """
    blocks: List[ScriptBlock] = []
    cursor = 0.0
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]

    skip_prefixes = (
        "EPISODE NUMBER:",
        "EPISODE LOGLINE:",
        "CONTINUITY NOTES:",
        "--- SCRIPT",
        "SCENE ",
        "SCENE HEADING:",
    )

    i = 0
    while i < len(lines):
        line = lines[i]
        upper_line = line.upper()
        if any(upper_line.startswith(p) for p in skip_prefixes):
            i += 1
            continue

        # Action/stage direction in brackets or parentheses
        if (line.startswith("[") and line.endswith("]")) or (line.startswith("(") and line.endswith(")")):
            inner = line[1:-1].strip()
            dur = max(1.8, min(6.0, len(inner.split()) / 2.8 + 0.8))
            btype = "SOUND FX" if any(k in inner.lower() for k in ("sfx", "sound", "music", "bang", "ring", "swell")) else "ACTION"
            blocks.append(ScriptBlock(btype, None, None, round(cursor, 2), round(cursor + dur, 2), inner, line))
            cursor += dur + 0.35
            i += 1
            continue

        # **SPEAKER (Tone):** followed by next line
        bold_spk = re.match(r"^\*\*([^*]+)\*\*:?\s*$", line)
        if bold_spk and i + 1 < len(lines):
            raw_hdr = bold_spk.group(1).strip().rstrip(":")
            body_line = lines[i + 1]
            dur = max(1.8, len(body_line.split()) / 2.4 + 0.6)
            if raw_hdr.upper() in ("CAMERA", "ACTION", "SOUND FX", "MUSIC"):
                blocks.append(ScriptBlock(raw_hdr.upper(), None, None, round(cursor, 2), round(cursor + dur, 2), body_line, f"{line}\n{body_line}"))
            else:
                speaker, tone = _extract_speaker_and_tone(raw_hdr)
                blocks.append(ScriptBlock("DIALOGUE", speaker, tone, round(cursor, 2), round(cursor + dur, 2), body_line, f"{line}\n{body_line}"))
            cursor += dur + 0.35
            i += 2
            continue

        # SPEAKER (Tone): dialogue
        spk_line = re.match(r"^([A-Za-z][A-Za-z0-9 .'\-()]{1,35}):\s+(.+)$", line)
        if spk_line:
            hdr = spk_line.group(1).strip()
            body_line = spk_line.group(2).strip()
            dur = max(1.8, len(body_line.split()) / 2.4 + 0.6)
            hdr_up = hdr.upper()
            if hdr_up in ("CAMERA", "ACTION", "SOUND FX", "SFX", "MUSIC"):
                btype = "SOUND FX" if hdr_up == "SFX" else hdr_up
                blocks.append(ScriptBlock(btype, None, None, round(cursor, 2), round(cursor + dur, 2), body_line, line))
            else:
                speaker, tone = _extract_speaker_and_tone(hdr)
                blocks.append(ScriptBlock("DIALOGUE", speaker, tone, round(cursor, 2), round(cursor + dur, 2), body_line, line))
            cursor += dur + 0.35
            i += 1
            continue

        # Plain narrative / prose sentence splitting if single huge paragraph
        if len(line.split()) > 35:
            sentences = re.split(r"(?<=[.!?])\s+", line)
            for sent in sentences:
                sent = sent.strip()
                if not sent:
                    continue
                dur = max(2.0, len(sent.split()) / 2.4 + 0.5)
                btype = "DIALOGUE" if ('"' in sent or "'" in sent) else "ACTION"
                spk = "NARRATOR" if btype == "DIALOGUE" else None
                blocks.append(ScriptBlock(btype, spk, None, round(cursor, 2), round(cursor + dur, 2), sent, sent))
                cursor += dur + 0.35
        else:
            dur = max(1.8, len(line.split()) / 2.4 + 0.5)
            blocks.append(ScriptBlock("DIALOGUE", "SPEAKER", None, round(cursor, 2), round(cursor + dur, 2), line, line))
            cursor += dur + 0.35
        i += 1

    return blocks


def parse_screenplay_text(
    content: str,
    source_name: str = "uploaded_input",
    default_ep_number: Optional[int] = None,
) -> Episode:
    """Parses screenplay, subtitle, or plain script text into a structured Episode."""
    normalized = content.replace("\r\n", "\n")

    ep_num = _infer_episode_number(normalized, source_name, default_ep_number)

    logline_match = re.search(r"EPISODE LOGLINE:\s*(.*?)(?=\n[A-Z\s]+:|\n---|\Z)", normalized, re.DOTALL)
    logline = logline_match.group(1).strip() if logline_match else ""

    cont_match = re.search(r"CONTINUITY NOTES:\s*(.*?)(?=\n--- SCRIPT START|\Z)", normalized, re.DOTALL)
    continuity = cont_match.group(1).strip() if cont_match else ""

    script_start = normalized.find("--- SCRIPT START ---")
    script_end = normalized.find("--- SCRIPT END ---")
    if script_start != -1:
        body = normalized[script_start + len("--- SCRIPT START ---"):script_end if script_end != -1 else len(normalized)]
    else:
        body = normalized

    source_format = "kuku_screenplay"
    timestamps_estimated = False

    blocks = _parse_kuku_blocks(body)
    if not blocks:
        srt_blocks = _parse_srt_blocks(body)
        if srt_blocks:
            blocks = srt_blocks
            source_format = "srt_subtitles"
    if not blocks:
        ts_blocks = _parse_inline_timestamp_blocks(body)
        if ts_blocks:
            blocks = ts_blocks
            source_format = "timestamped_transcript"
    if not blocks:
        blocks = _parse_plain_script_blocks(body)
        source_format = "plain_script_estimated"
        timestamps_estimated = True

    blocks.sort(key=lambda b: (b.start_time, b.end_time))

    if not logline and blocks:
        first_dialogue = next((b.content for b in blocks if b.block_type == "DIALOGUE" and b.content), "")
        if first_dialogue:
            logline = f"Starts with: \"{first_dialogue[:140]}\""

    return Episode(
        ep_number=ep_num,
        title=f"Episode {ep_num}",
        logline=logline,
        continuity=continuity,
        blocks=blocks,
        raw_path=source_name,
        source_format=source_format,
        timestamps_estimated=timestamps_estimated,
    )


def parse_screenplay_file(filepath: str, default_ep_number: Optional[int] = None) -> Episode:
    """Parses an episode screenplay text file into a structured Episode object."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return parse_screenplay_text(content, source_name=filepath, default_ep_number=default_ep_number)
