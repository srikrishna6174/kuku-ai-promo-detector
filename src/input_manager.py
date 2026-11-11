import csv
import glob
import io
import json
import os
import re
import shutil
import uuid
import zipfile
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.detector import (
    PromoCandidate,
    build_manual_promo_candidate,
    find_promos_for_episode,
    generate_curated_multi_segment_promos,
)
from src.export_utils import generate_ffmpeg_commands
from src.llm_refiner import LLMProviderConfig, detect_promos_with_llms
from src.parser import Episode, ScriptBlock, format_time, parse_screenplay_file, parse_screenplay_text, parse_time_str
from src.quality_checker import run_season_quality_audit
from src.ranker import rank_promos

SAVED_INPUTS_DIR = "saved_inputs"
BUILTIN_INPUT_ID = "builtin_duke"


def _natural_sort_key(text: str):
    return [int(tok) if tok.isdigit() else tok.lower() for tok in re.split(r"(\d+)", text or "")]


def _safe_slug(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", (title or "input").strip()).strip("_").lower()
    return slug[:36] or "input"


def serialize_episode(ep: Episode) -> Dict[str, Any]:
    d = ep.to_dict()
    d["blocks"] = [b.to_dict() for b in ep.blocks]
    return d


def deserialize_episode(ep_dict: Dict[str, Any]) -> Episode:
    blocks = [
        ScriptBlock(
            block_type=b.get("block_type", "DIALOGUE"),
            speaker=b.get("speaker"),
            tone=b.get("tone"),
            start_time=float(b.get("start_time", 0.0)),
            end_time=float(b.get("end_time", 0.0)),
            content=b.get("content", ""),
        )
        for b in ep_dict.get("blocks", [])
    ]
    return Episode(
        ep_number=int(ep_dict.get("episode_number", 1)),
        title=ep_dict.get("title", f"Episode {ep_dict.get('episode_number', 1)}"),
        logline=ep_dict.get("logline", ""),
        continuity=ep_dict.get("continuity", ""),
        blocks=blocks,
        raw_path=ep_dict.get("raw_path", "saved"),
        source_format=ep_dict.get("source_format", "kuku_screenplay"),
        timestamps_estimated=bool(ep_dict.get("timestamps_estimated", False)),
    )


def serialize_promo_candidate(p: PromoCandidate) -> Dict[str, Any]:
    return {
        "rank": p.rank,
        "episode": p.episode_number,
        "segments": [
            {
                "segment_index": 1,
                "start_time": format_time(p.start_time),
                "end_time": format_time(p.end_time),
                "duration_seconds": p.duration,
            }
        ],
        "start_seconds": p.start_time,
        "end_seconds": p.end_time,
        "total_duration_seconds": p.duration,
        "marketing_tier": p.funnel_type,
        "total_score": p.total_score,
        "hook_score": round(p.hook_score, 1),
        "cliffhanger_score": round(p.cliffhanger_score, 1),
        "coherence_score": round(p.coherence_score, 1),
        "hook": p.hook_description,
        "cliffhanger": p.cliffhanger_description,
        "why_it_works": p.why_it_works,
        "detection_method": p.detection_method,
        "proposed_by": p.proposed_by,
        "model_scores": p.model_scores,
        "judge_verdict": p.judge_verdict,
        "script_excerpt": [
            {
                "start": b.start_formatted,
                "end": b.end_formatted,
                "type": b.block_type,
                "speaker": b.speaker,
                "tone": b.tone,
                "content": b.content,
            }
            for b in p.blocks
        ],
    }


def parse_uploaded_sources(
    uploaded_files: Optional[List[Any]] = None,
    pasted_text: str = "",
) -> Tuple[List[Episode], str]:
    """
    Parses uploaded .txt/.srt/.zip files or pasted script text into Episode objects.
    Returns (episodes, suggested_title).
    """
    raw_entries: List[Tuple[str, str]] = []  # (filename, content)

    if uploaded_files:
        for uf in uploaded_files:
            fname = getattr(uf, "name", "uploaded.txt")
            raw_bytes = uf.getvalue() if hasattr(uf, "getvalue") else uf.read()
            if fname.lower().endswith(".zip"):
                try:
                    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
                        members = [
                            m
                            for m in zf.namelist()
                            if not m.endswith("/")
                            and "__MACOSX" not in m
                            and not os.path.basename(m).startswith(".")
                            and m.lower().endswith((".txt", ".srt", ".vtt", ".md"))
                        ]
                        members.sort(key=_natural_sort_key)
                        for m in members:
                            text = zf.read(m).decode("utf-8", errors="ignore")
                            if text.strip():
                                raw_entries.append((os.path.basename(m), text))
                except zipfile.BadZipFile as exc:
                    raise ValueError(f"Invalid ZIP archive '{fname}': {exc}") from exc
            else:
                text = raw_bytes.decode("utf-8", errors="ignore")
                if text.strip():
                    raw_entries.append((os.path.basename(fname), text))

    if pasted_text and pasted_text.strip():
        raw_entries.append(("pasted_script.txt", pasted_text.strip()))

    if not raw_entries:
        return [], "Untitled Input"

    raw_entries.sort(key=lambda item: _natural_sort_key(item[0]))
    episodes: List[Episode] = []
    seen_ep_nums = set()

    for idx, (fname, text) in enumerate(raw_entries, 1):
        ep = parse_screenplay_text(text, source_name=fname, default_ep_number=idx)
        # Ensure distinct episode numbers when multiple files lack episode headers
        if ep.ep_number in seen_ep_nums:
            ep.ep_number = max(seen_ep_nums) + 1
            ep.title = f"Episode {ep.ep_number}"
        seen_ep_nums.add(ep.ep_number)
        if ep.blocks:
            episodes.append(ep)

    episodes.sort(key=lambda e: e.ep_number)

    if uploaded_files:
        first_name = os.path.splitext(os.path.basename(getattr(uploaded_files[0], "name", "Uploaded Script")))[0]
        suggested_title = first_name.replace("_", " ").replace("-", " ").strip().title()
        if len(episodes) > 1 and not getattr(uploaded_files[0], "name", "").lower().endswith(".zip"):
            suggested_title = f"{suggested_title} ({len(episodes)} Episodes)"
    else:
        suggested_title = f"Pasted Script ({datetime.now().strftime('%H:%M')})"

    return episodes, suggested_title or "New Script Input"


def parse_uploaded_files_as_separate_inputs(uploaded_files: List[Any]) -> List[Tuple[List[Episode], str]]:
    """Parses each uploaded .txt/.srt file into its own standalone (episodes, title) pair."""
    batches: List[Tuple[List[Episode], str]] = []
    for uf in uploaded_files or []:
        fname = getattr(uf, "name", "uploaded.txt")
        if fname.lower().endswith(".zip"):
            eps, title = parse_uploaded_sources(uploaded_files=[uf])
            if eps:
                batches.append((eps, title))
            continue
        raw_bytes = uf.getvalue() if hasattr(uf, "getvalue") else uf.read()
        text = raw_bytes.decode("utf-8", errors="ignore")
        if not text.strip():
            continue
        ep = parse_screenplay_text(text, source_name=os.path.basename(fname), default_ep_number=1)
        if ep.blocks:
            title = os.path.splitext(os.path.basename(fname))[0].replace("_", " ").replace("-", " ").strip().title()
            batches.append(([ep], title or "Uploaded Script"))
    return batches


def process_episodes_into_bundle(
    episodes: List[Episode],
    title: str,
    detection_mode: str = "manual",  # 'manual', 'llm', 'both'
    min_duration: float = 20.0,
    max_duration: float = 60.0,
    top_k_per_ep: int = 2,
    custom_hook_keywords: Optional[List[str]] = None,
    custom_cliffhanger_keywords: Optional[List[str]] = None,
    custom_only: bool = False,
    cliffhanger_style: str = "any",
    llm_providers: Optional[List[LLMProviderConfig]] = None,
    use_judge: bool = False,
    judge_provider_name: str = "auto",
    run_all_active_llms: bool = True,
    manual_cuts: Optional[List[Dict[str, Any]]] = None,
    is_saved: bool = False,
) -> Dict[str, Any]:
    """Runs the selected promo detection pipeline on arbitrary parsed episodes."""
    all_promos: List[PromoCandidate] = []
    episodes_map: Dict[int, Episode] = {ep.ep_number: ep for ep in episodes}

    telemetry_summary: Dict[str, Any] = {
        "mode": detection_mode,
        "providers_configured": [p.display_name for p in (llm_providers or []) if p.enabled],
        "providers_succeeded": [],
        "provider_failures": [],
        "failover_triggered": False,
        "judge_used": False,
        "judge_providers": [],
        "judge_failures": [],
        "all_llms_failed": False,
    }

    for ep in episodes:
        manual_cands: List[PromoCandidate] = []
        if detection_mode in ("manual", "both"):
            manual_cands = find_promos_for_episode(
                ep,
                min_duration=min_duration,
                max_duration=max_duration,
                top_k=top_k_per_ep,
                custom_hook_keywords=custom_hook_keywords,
                custom_cliffhanger_keywords=custom_cliffhanger_keywords,
                custom_only=custom_only,
                cliffhanger_style=cliffhanger_style,
            )

        if detection_mode == "manual":
            ep_promos = manual_cands
        else:
            ep_promos, ep_tel = detect_promos_with_llms(
                episode=ep,
                providers=llm_providers or [],
                min_duration=min_duration,
                max_duration=max_duration,
                top_k=top_k_per_ep,
                manual_candidates=manual_cands,
                use_judge=use_judge,
                judge_provider_name=judge_provider_name,
                detection_mode=detection_mode,
                run_all_active_llms=run_all_active_llms,
            )
            _merge_episode_telemetry(telemetry_summary, ep_tel)

        all_promos.extend(ep_promos)

    # Apply any user-pinned manual cuts
    if manual_cuts:
        for mc in manual_cuts:
            ep_num = int(mc.get("episode", episodes[0].ep_number if episodes else 1))
            target_ep = episodes_map.get(ep_num)
            if target_ep:
                pinned = build_manual_promo_candidate(
                    target_ep,
                    start_time=float(mc["start_time"]),
                    end_time=float(mc["end_time"]),
                    hook_note=mc.get("hook_note", ""),
                    cliffhanger_note=mc.get("cliffhanger_note", ""),
                )
                if pinned:
                    all_promos.append(pinned)

    ranked_promos = rank_promos(all_promos, total_episodes=len(episodes))
    stitched_promos = generate_curated_multi_segment_promos(
        episodes_map, show_title=title, promos=ranked_promos
    )
    audit_report = run_season_quality_audit(ranked_promos, episodes=episodes)

    mode_labels = {
        "manual": "Manual / Rule-Based Cuts",
        "llm": "Multi-LLM Detection",
        "both": "Hybrid (Manual Cuts + LLM)",
    }
    if telemetry_summary["judge_used"]:
        mode_label = f"{mode_labels.get(detection_mode, detection_mode)} + Judge"
    else:
        mode_label = mode_labels.get(detection_mode, detection_mode)

    input_id = f"{_safe_slug(title)}_{uuid.uuid4().hex[:6]}"
    bundle: Dict[str, Any] = {
        "id": input_id,
        "title": title.strip() or "Untitled Input",
        "is_builtin": False,
        "is_saved": is_saved,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "detection_mode": detection_mode,
        "detection_label": mode_label,
        "episode_count": len(episodes),
        "promo_count": len(ranked_promos),
        "promos": [serialize_promo_candidate(p) for p in ranked_promos],
        "stitched_promos": stitched_promos,
        "audit_report": audit_report,
        "episodes": [serialize_episode(ep) for ep in episodes],
        "telemetry": telemetry_summary,
    }
    return bundle


def _promo_dict_to_candidate(pd_item: Dict[str, Any], ep_obj: Episode) -> Optional[PromoCandidate]:
    """Converts a serialized promo dict back into a PromoCandidate using its Episode blocks."""
    seg = (pd_item.get("segments") or [{}])[0]
    try:
        s_t = float(pd_item.get("start_seconds", parse_time_str(seg.get("start_time", "00:00.00"))))
        e_t = float(pd_item.get("end_seconds", parse_time_str(seg.get("end_time", "00:30.00"))))
    except Exception:
        s_t, e_t = 0.0, 30.0

    blks = [b for b in ep_obj.blocks if b.end_time > s_t + 0.05 and b.start_time < e_t - 0.05]
    if not blks:
        blks = ep_obj.blocks[:1]
    if not blks:
        return None

    cand = PromoCandidate(
        episode_number=ep_obj.ep_number,
        start_time=s_t,
        end_time=e_t,
        hook_block=blks[0],
        cliffhanger_block=blks[-1],
        blocks_in_range=blks,
        hook_score=float(pd_item.get("hook_score", 7.0)),
        cliffhanger_score=float(pd_item.get("cliffhanger_score", 7.0)),
        coherence_score=float(pd_item.get("coherence_score", 7.0)),
        detection_method=pd_item.get("detection_method", "Rule-Based"),
        proposed_by=list(pd_item.get("proposed_by") or [pd_item.get("detection_method", "Rule-Based")]),
        model_scores=dict(pd_item.get("model_scores") or {}),
        judge_verdict=pd_item.get("judge_verdict"),
    )
    cand.total_score = float(pd_item.get("total_score", cand.total_score))
    cand.hook_description = str(pd_item.get("hook", ""))
    cand.cliffhanger_description = str(pd_item.get("cliffhanger", ""))
    cand.why_it_works = str(pd_item.get("why_it_works", ""))
    cand.funnel_type = str(pd_item.get("marketing_tier", ""))
    cand.rank = int(pd_item.get("rank", 0))
    return cand


def _merge_episode_telemetry(summary: Dict[str, Any], ep_tel: Dict[str, Any]) -> None:
    for ps in ep_tel.get("providers_succeeded", []):
        if ps not in summary["providers_succeeded"]:
            summary["providers_succeeded"].append(ps)
    summary["provider_failures"].extend(ep_tel.get("provider_failures", []))
    if ep_tel.get("failover_triggered"):
        summary["failover_triggered"] = True
    if ep_tel.get("judge_used"):
        summary["judge_used"] = True
        jp = ep_tel.get("judge_provider")
        if jp and jp not in summary["judge_providers"]:
            summary["judge_providers"].append(jp)
    summary["judge_failures"].extend(ep_tel.get("judge_failures", []))
    if ep_tel.get("all_llms_failed"):
        summary["all_llms_failed"] = True


def _load_bundle_episodes(bundle: Dict[str, Any]) -> List[Episode]:
    ep_dicts = bundle.get("episodes", [])
    if ep_dicts:
        return [deserialize_episode(e) for e in ep_dicts]
    ep_files = bundle.get("ep_files", [])
    if ep_files:
        return [parse_screenplay_file(f) for f in ep_files]
    return []


def enhance_bundle_with_ai(
    bundle: Dict[str, Any],
    llm_providers: List[LLMProviderConfig],
    target_episodes: Optional[List[int]] = None,
    action: str = "merge",  # 'merge', 'replace', 'judge_only'
    min_duration: float = 20.0,
    max_duration: float = 60.0,
    top_k_per_ep: int = 2,
    use_judge: bool = True,
    judge_provider_name: str = "auto",
    run_all_active_llms: bool = True,
    progress_cb: Optional[Callable[[int, int, int], None]] = None,
    base_dir: str = SAVED_INPUTS_DIR,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Runs AI promo generation or LLM-as-a-Judge refinement inside an existing project
    (even if originally created in offline/rule-based mode).
    """
    episodes = _load_bundle_episodes(bundle)
    if not episodes:
        raise ValueError("No episode script blocks are available in this project to run AI generation.")

    ep_by_num: Dict[int, Episode] = {ep.ep_number: ep for ep in episodes}
    target_set = set(target_episodes) if target_episodes else set(ep_by_num.keys())
    ordered_targets = [ep_by_num[num] for num in sorted(target_set) if num in ep_by_num]
    if not ordered_targets:
        raise ValueError("None of the selected episodes were found in this project.")

    existing_cands: List[PromoCandidate] = []
    for pd_item in bundle.get("promos", []):
        ep_o = ep_by_num.get(int(pd_item.get("episode", 1)))
        if not ep_o:
            continue
        cand = _promo_dict_to_candidate(pd_item, ep_o)
        if cand is not None:
            existing_cands.append(cand)

    telemetry_summary: Dict[str, Any] = {
        "mode": "both" if action == "merge" else "llm",
        "providers_configured": [p.display_name for p in llm_providers if p.enabled],
        "providers_succeeded": [],
        "provider_failures": [],
        "failover_triggered": False,
        "judge_used": False,
        "judge_providers": [],
        "judge_failures": [],
        "all_llms_failed": False,
    }

    retained_cands = [c for c in existing_cands if c.episode_number not in target_set]
    new_target_cands: List[PromoCandidate] = []

    from src.llm_refiner import _run_llm_judge

    total_steps = len(ordered_targets)
    for step_idx, ep in enumerate(ordered_targets, 1):
        if progress_cb is not None:
            progress_cb(step_idx, total_steps, ep.ep_number)

        ep_existing = [c for c in existing_cands if c.episode_number == ep.ep_number]
        if action == "judge_only":
            if ep_existing:
                judged, used_j, j_attempts = _run_llm_judge(ep, ep_existing, llm_providers, min_duration, max_duration)
                for ja in j_attempts:
                    if ja["status"] == "failed":
                        telemetry_summary["judge_failures"].append({"provider": ja["provider"], "error": ja["error"]})
                if used_j:
                    telemetry_summary["judge_used"] = True
                    jp_label = f"{used_j.display_name} ({used_j.model})"
                    if jp_label not in telemetry_summary["judge_providers"]:
                        telemetry_summary["judge_providers"].append(jp_label)
                    if used_j.display_name not in telemetry_summary["providers_succeeded"]:
                        telemetry_summary["providers_succeeded"].append(used_j.display_name)
                elif j_attempts:
                    telemetry_summary["all_llms_failed"] = True
                new_target_cands.extend(judged)
        else:
            ep_promos, ep_tel = detect_promos_with_llms(
                episode=ep,
                providers=llm_providers,
                min_duration=min_duration,
                max_duration=max_duration,
                top_k=top_k_per_ep,
                manual_candidates=ep_existing if action == "merge" else None,
                use_judge=use_judge,
                judge_provider_name=judge_provider_name,
                detection_mode="both" if action == "merge" else "llm",
                run_all_active_llms=run_all_active_llms,
            )
            _merge_episode_telemetry(telemetry_summary, ep_tel)
            new_target_cands.extend(ep_promos)

    combined = retained_cands + new_target_cands
    ranked = rank_promos(combined, total_episodes=len(episodes))

    is_from_builtin = bool(bundle.get("is_builtin"))
    out_title = f"{bundle.get('title', 'Project')} (AI Enhanced)" if is_from_builtin else bundle.get("title", "Project")
    stitched = generate_curated_multi_segment_promos(ep_by_num, show_title=out_title, promos=ranked)
    audit_report = run_season_quality_audit(ranked, episodes=episodes)

    label = "Hybrid (Rules + AI)" if action == "merge" else ("AI Judged" if action == "judge_only" else "Multi-LLM Detection")
    if telemetry_summary["judge_used"] and "Judge" not in label:
        label = f"{label} + Judge"

    if is_from_builtin:
        updated: Dict[str, Any] = {
            "id": f"{_safe_slug(out_title)}_{uuid.uuid4().hex[:6]}",
            "title": out_title,
            "is_builtin": False,
            "is_saved": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "detection_mode": telemetry_summary["mode"],
            "detection_label": label,
            "episode_count": len(episodes),
            "promo_count": len(ranked),
            "promos": [serialize_promo_candidate(p) for p in ranked],
            "stitched_promos": stitched,
            "audit_report": audit_report,
            "episodes": [serialize_episode(ep) for ep in episodes],
            "telemetry": telemetry_summary,
        }
    else:
        updated = bundle
        updated["detection_mode"] = telemetry_summary["mode"]
        updated["detection_label"] = label
        updated["promo_count"] = len(ranked)
        updated["promos"] = [serialize_promo_candidate(p) for p in ranked]
        updated["stitched_promos"] = stitched
        updated["audit_report"] = audit_report
        updated["telemetry"] = telemetry_summary
        if updated.get("is_saved"):
            save_bundle_to_disk(updated, base_dir=base_dir)

    return updated, telemetry_summary


def add_manual_cut_to_bundle(
    bundle: Dict[str, Any],
    episode_number: int,
    start_time: float,
    end_time: float,
    hook_note: str = "",
    cliffhanger_note: str = "",
    base_dir: str = SAVED_INPUTS_DIR,
) -> Tuple[bool, str]:
    """Pins a manual promo cut into an existing bundle and refreshes rankings/audit."""
    ep_dicts = bundle.get("episodes", [])
    target_ep_dict = next((e for e in ep_dicts if int(e.get("episode_number", -1)) == int(episode_number)), None)
    if not target_ep_dict:
        return False, f"Episode {episode_number} script blocks are unavailable for manual cutting."

    ep_obj = deserialize_episode(target_ep_dict)
    pinned = build_manual_promo_candidate(
        ep_obj,
        start_time=start_time,
        end_time=end_time,
        hook_note=hook_note,
        cliffhanger_note=cliffhanger_note,
    )
    if not pinned:
        return False, "Invalid time range or no script blocks found in that window."

    new_promo_dict = serialize_promo_candidate(pinned)
    promos = list(bundle.get("promos", []))
    promos.append(new_promo_dict)

    # Re-sort and reassign ranks cleanly
    def score_key(d: Dict[str, Any]) -> float:
        jv = d.get("judge_verdict") or {}
        if isinstance(jv.get("judge_score"), (int, float)):
            return float(jv["judge_score"])
        return float(d.get("total_score", 0))

    promos.sort(key=score_key, reverse=True)
    n = len(promos)
    t1_cut = max(1, round(n * 0.35))
    t2_cut = max(t1_cut, round(n * 0.70))
    is_full = bundle.get("episode_count", 1) >= 6

    for idx, p in enumerate(promos, 1):
        p["rank"] = idx
        if not p.get("marketing_tier"):
            if is_full:
                if p.get("episode") in (1, 2, 3):
                    p["marketing_tier"] = "Tier 1: Top-of-Funnel (Cold UA) - Post First"
                elif idx <= 15:
                    p["marketing_tier"] = "Tier 2: High-Engagement Escalation - Post Second"
                else:
                    p["marketing_tier"] = "Tier 3: Retargeting & Cliffhanger Drive - Post Third"
            else:
                if idx <= t1_cut and score_key(p) >= 65:
                    p["marketing_tier"] = "Tier 1: Top-of-Funnel (Cold UA) - Post First"
                elif idx <= t2_cut:
                    p["marketing_tier"] = "Tier 2: High-Engagement Escalation - Post Second"
                else:
                    p["marketing_tier"] = "Tier 3: Retargeting & Cliffhanger Drive - Post Third"

    bundle["promos"] = promos
    bundle["promo_count"] = len(promos)

    # Keep quality audit synchronized when a manual cut is added
    try:
        ep_objs = [deserialize_episode(e) for e in ep_dicts]
        ep_by_num = {ep.ep_number: ep for ep in ep_objs}
        promo_objs = [
            c for c in (_promo_dict_to_candidate(pd_item, ep_by_num[int(pd_item.get("episode", 1))]) for pd_item in promos if int(pd_item.get("episode", 1)) in ep_by_num)
            if c is not None
        ]
        if promo_objs:
            bundle["audit_report"] = run_season_quality_audit(promo_objs, episodes=ep_objs)
    except Exception:
        pass

    if bundle.get("is_saved") and not bundle.get("is_builtin"):
        save_bundle_to_disk(bundle, base_dir=base_dir)

    return True, f"Pinned manual cut ({format_time(pinned.start_time)} - {format_time(pinned.end_time)}) as Rank #{new_promo_dict.get('rank', '?')}."


def pin_manual_cut_any_bundle(
    bundle: Dict[str, Any],
    episode_number: int,
    start_time: float,
    end_time: float,
    hook_note: str = "",
    cliffhanger_note: str = "",
    base_dir: str = SAVED_INPUTS_DIR,
) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Pins a manual timestamp cut into ANY bundle (AI-only, rule-based, or built-in benchmark).
    Clones the built-in benchmark into a working draft before modifying it so outputs stay intact.
    """
    if bundle.get("is_builtin"):
        episodes = _load_bundle_episodes(bundle)
        if not episodes:
            return False, "Built-in episode script files could not be loaded.", bundle
        clone_title = f"{bundle.get('title', 'Project')} (Custom Cuts)"
        target: Dict[str, Any] = {
            "id": f"{_safe_slug(clone_title)}_{uuid.uuid4().hex[:6]}",
            "title": clone_title,
            "is_builtin": False,
            "is_saved": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "detection_mode": bundle.get("detection_mode", "manual"),
            "detection_label": bundle.get("detection_label", "Custom Cuts"),
            "episode_count": len(episodes) or int(bundle.get("episode_count", 1)),
            "promo_count": len(bundle.get("promos", [])),
            "promos": [dict(p) for p in bundle.get("promos", [])],
            "stitched_promos": list(bundle.get("stitched_promos", [])),
            "audit_report": dict(bundle.get("audit_report", {})),
            "episodes": [serialize_episode(ep) for ep in episodes],
            "telemetry": dict(bundle.get("telemetry", {})),
        }
    else:
        target = bundle
        if not target.get("episodes") and target.get("ep_files"):
            target["episodes"] = [serialize_episode(ep) for ep in _load_bundle_episodes(target)]

    ok, msg = add_manual_cut_to_bundle(
        target,
        episode_number=episode_number,
        start_time=start_time,
        end_time=end_time,
        hook_note=hook_note,
        cliffhanger_note=cliffhanger_note,
        base_dir=base_dir,
    )
    return ok, msg, (target if ok else bundle)


def add_rule_based_promos_to_bundle(
    bundle: Dict[str, Any],
    min_duration: float = 20.0,
    max_duration: float = 60.0,
    top_k_per_ep: int = 2,
    base_dir: str = SAVED_INPUTS_DIR,
) -> Tuple[Dict[str, Any], int]:
    """Generates and merges fast rule-based promo cuts into an existing (e.g. AI-first) project."""
    episodes = _load_bundle_episodes(bundle)
    if not episodes:
        raise ValueError("No episode script blocks are available in this project to generate rule-based cuts.")

    ep_by_num: Dict[int, Episode] = {ep.ep_number: ep for ep in episodes}
    existing_cands: List[PromoCandidate] = []
    seen_windows = set()
    for pd_item in bundle.get("promos", []):
        ep_o = ep_by_num.get(int(pd_item.get("episode", 1)))
        if not ep_o:
            continue
        cand = _promo_dict_to_candidate(pd_item, ep_o)
        if cand is not None:
            existing_cands.append(cand)
            seen_windows.add((cand.episode_number, round(cand.start_time, 1), round(cand.end_time, 1)))

    added = 0
    new_rules: List[PromoCandidate] = []
    for ep in episodes:
        rule_cands = find_promos_for_episode(
            ep,
            min_duration=min_duration,
            max_duration=max_duration,
            top_k=top_k_per_ep,
        )
        for rc in rule_cands:
            key = (rc.episode_number, round(rc.start_time, 1), round(rc.end_time, 1))
            if key not in seen_windows:
                seen_windows.add(key)
                new_rules.append(rc)
                added += 1

    combined = existing_cands + new_rules
    ranked = rank_promos(combined, total_episodes=len(episodes))

    is_from_builtin = bool(bundle.get("is_builtin"))
    out_title = f"{bundle.get('title', 'Project')} (With Rule Cuts)" if is_from_builtin else bundle.get("title", "Project")
    stitched = generate_curated_multi_segment_promos(ep_by_num, show_title=out_title, promos=ranked)
    audit_report = run_season_quality_audit(ranked, episodes=episodes)

    had_ai = any(
        "llm" in str(p.get("detection_method", "")).lower() or bool(p.get("judge_verdict"))
        for p in bundle.get("promos", [])
    )
    new_label = "Hybrid (Rules + AI)" if had_ai else "Manual / Rule-Based Cuts"

    updated: Dict[str, Any] = {
        **(
            {
                "id": f"{_safe_slug(out_title)}_{uuid.uuid4().hex[:6]}",
                "title": out_title,
                "is_builtin": False,
                "is_saved": False,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            if is_from_builtin
            else bundle
        ),
        "detection_mode": "both" if had_ai else "manual",
        "detection_label": new_label,
        "episode_count": len(episodes),
        "promo_count": len(ranked),
        "promos": [serialize_promo_candidate(p) for p in ranked],
        "stitched_promos": stitched,
        "audit_report": audit_report,
        "episodes": [serialize_episode(ep) for ep in episodes],
    }
    if updated.get("is_saved") and not updated.get("is_builtin"):
        save_bundle_to_disk(updated, base_dir=base_dir)

    return updated, added


def load_builtin_bundle(
    data_folder: str = "I Married a Broken Soldier. He was a Duke",
    output_dir: str = "outputs",
) -> Dict[str, Any]:
    """Loads the precomputed benchmark show into the unified bundle structure."""
    json_path = os.path.join(output_dir, "promos_master.json")
    audit_path = os.path.join(output_dir, "quality_audit_and_failures.json")

    promos_data: List[Dict[str, Any]] = []
    stitched_data: List[Dict[str, Any]] = []
    audit_data: Dict[str, Any] = {}
    show_title = "I Married a Broken Soldier. He was a Duke"
    ep_count = 50

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            full_j = json.load(f)
            promos_data = full_j.get("promos", [])
            stitched_data = full_j.get("multi_segment_stitched_promos", [])
            show_title = full_j.get("show_title", show_title)
            ep_count = full_j.get("total_episodes_processed", ep_count)

    for p in promos_data:
        p.setdefault("detection_method", "Precomputed Rule-Based")
        p.setdefault("proposed_by", ["Rule-Based Pipeline"])

    if os.path.exists(audit_path):
        with open(audit_path, "r", encoding="utf-8") as f:
            audit_data = json.load(f)

    ep_files = sorted(glob.glob(os.path.join(data_folder, "*.txt"))) if os.path.exists(data_folder) else []

    return {
        "id": BUILTIN_INPUT_ID,
        "title": show_title,
        "is_builtin": True,
        "is_saved": True,
        "created_at": "Built-in Benchmark",
        "detection_mode": "manual",
        "detection_label": "Precomputed Benchmark",
        "episode_count": max(ep_count, len(ep_files)) if ep_files else ep_count,
        "promo_count": len(promos_data),
        "promos": promos_data,
        "stitched_promos": stitched_data,
        "audit_report": audit_data,
        "episodes": [],  # Loaded lazily from ep_files in UI for speed
        "ep_files": ep_files,
        "telemetry": {
            "mode": "precomputed",
            "providers_configured": [],
            "providers_succeeded": [],
            "provider_failures": [],
            "failover_triggered": False,
            "judge_used": False,
        },
    }


def save_bundle_to_disk(bundle: Dict[str, Any], base_dir: str = SAVED_INPUTS_DIR) -> Dict[str, Any]:
    """Persists an uploaded input bundle (metadata, promos, audit, parsed episodes) to disk."""
    os.makedirs(base_dir, exist_ok=True)
    bundle["is_saved"] = True
    bundle_dir = os.path.join(base_dir, bundle["id"])
    os.makedirs(bundle_dir, exist_ok=True)

    meta = {
        "id": bundle["id"],
        "title": bundle["title"],
        "created_at": bundle.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M")),
        "detection_mode": bundle.get("detection_mode", "manual"),
        "detection_label": bundle.get("detection_label", "Rule-Based"),
        "episode_count": bundle.get("episode_count", len(bundle.get("episodes", []))),
        "promo_count": len(bundle.get("promos", [])),
    }
    results = {
        "promos": bundle.get("promos", []),
        "stitched_promos": bundle.get("stitched_promos", []),
        "audit_report": bundle.get("audit_report", {}),
        "telemetry": bundle.get("telemetry", {}),
    }

    with open(os.path.join(bundle_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    with open(os.path.join(bundle_dir, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    with open(os.path.join(bundle_dir, "episodes.json"), "w", encoding="utf-8") as f:
        json.dump(bundle.get("episodes", []), f, indent=2)

    return bundle


def list_saved_inputs(base_dir: str = SAVED_INPUTS_DIR) -> List[Dict[str, Any]]:
    """Lists metadata for all user-saved inputs sorted newest-first."""
    if not os.path.exists(base_dir):
        return []
    metas: List[Dict[str, Any]] = []
    for entry in os.listdir(base_dir):
        meta_path = os.path.join(base_dir, entry, "meta.json")
        if os.path.isfile(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    metas.append(json.load(f))
            except Exception:
                continue
    metas.sort(key=lambda m: m.get("created_at", ""), reverse=True)
    return metas


def load_saved_bundle(input_id: str, base_dir: str = SAVED_INPUTS_DIR) -> Optional[Dict[str, Any]]:
    """Loads a saved input bundle from disk."""
    bundle_dir = os.path.join(base_dir, input_id)
    meta_path = os.path.join(bundle_dir, "meta.json")
    results_path = os.path.join(bundle_dir, "results.json")
    episodes_path = os.path.join(bundle_dir, "episodes.json")

    if not os.path.isfile(meta_path) or not os.path.isfile(results_path):
        return None

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)
    episodes = []
    if os.path.isfile(episodes_path):
        with open(episodes_path, "r", encoding="utf-8") as f:
            episodes = json.load(f)

    return {
        "id": meta["id"],
        "title": meta["title"],
        "is_builtin": False,
        "is_saved": True,
        "created_at": meta.get("created_at", ""),
        "detection_mode": meta.get("detection_mode", "manual"),
        "detection_label": meta.get("detection_label", ""),
        "episode_count": meta.get("episode_count", len(episodes)),
        "promo_count": len(results.get("promos", [])),
        "promos": results.get("promos", []),
        "stitched_promos": results.get("stitched_promos", []),
        "audit_report": results.get("audit_report", {}),
        "episodes": episodes,
        "telemetry": results.get("telemetry", {}),
    }


def delete_saved_bundle(input_id: str, base_dir: str = SAVED_INPUTS_DIR) -> bool:
    bundle_dir = os.path.join(base_dir, input_id)
    if os.path.isdir(bundle_dir):
        shutil.rmtree(bundle_dir, ignore_errors=True)
        return True
    return False


def is_builtin_hidden(base_dir: str = SAVED_INPUTS_DIR) -> bool:
    return os.path.isfile(os.path.join(base_dir, ".hide_builtin"))


def set_builtin_hidden(hidden: bool, base_dir: str = SAVED_INPUTS_DIR) -> None:
    marker = os.path.join(base_dir, ".hide_builtin")
    if hidden:
        os.makedirs(base_dir, exist_ok=True)
        with open(marker, "w", encoding="utf-8") as f:
            f.write("1")
    else:
        if os.path.isfile(marker):
            os.remove(marker)


def format_single_promo_txt(p: Dict[str, Any], show_title: str = "") -> str:
    """Formats a single promo candidate as a detailed, editor-ready plain-text cut sheet."""
    segments = p.get("segments") or [{}]
    ep_fallback = int(p.get("episode", 1))
    seg_eps = [int(s.get("episode", ep_fallback)) for s in segments]
    unique_eps = sorted(set(seg_eps))
    is_intercut = len(segments) > 1
    if is_intercut:
        intercut_type = (
            f"Yes — Cross-Episode Intercut ({len(segments)} segments across Episodes {', '.join(str(e) for e in unique_eps)})"
            if len(unique_eps) > 1
            else f"Yes — Intra-Episode Jumpcut / Intercut ({len(segments)} segments in Episode {unique_eps[0]})"
        )
    else:
        intercut_type = f"No — Single Continuous Cut (Episode {unique_eps[0]})"

    ep_summary = ", ".join(f"Episode {e}" for e in unique_eps)
    tier_txt = p.get("marketing_tier", "")
    lines = [
        "=" * 72,
        f"PROMO RANK #{p.get('rank', '?')}  |  Score: {p.get('total_score', 0)}/100  |  Duration: {p.get('total_duration_seconds', 0)}s",
        "=" * 72,
    ]
    if show_title:
        lines.append(f"Project / Show   : {show_title}")
    lines.extend(
        [
            f"Source Episode(s): {ep_summary}",
            f"Intercut         : {intercut_type}",
            f"Marketing Tier   : {tier_txt}",
            f"Detection Method : {p.get('detection_method', 'Rule-Based')}",
        ]
    )
    if p.get("proposed_by"):
        lines.append(f"Detected By      : {', '.join(p['proposed_by'])}")

    score_parts = [
        f"Hook {p.get('hook_score', '-')}/10",
        f"Cliffhanger {p.get('cliffhanger_score', '-')}/10",
    ]
    if p.get("coherence_score") is not None:
        score_parts.append(f"Coherence {p.get('coherence_score')}/10")
    lines.append(f"Score Breakdown  : {' | '.join(score_parts)}")

    lines.append("")
    lines.append("CUT TIMECODES:")
    for idx, seg in enumerate(segments, 1):
        s_ep = seg.get("episode", ep_fallback)
        s_start = seg.get("start_time", "00:00.00")
        s_end = seg.get("end_time", "00:00.00")
        s_dur = seg.get("duration_seconds", p.get("total_duration_seconds", 0))
        lines.append(f"  Segment {idx}: Episode {s_ep} | {s_start} -> {s_end} ({s_dur}s)")

    lines.extend(
        [
            "",
            f"0-3s Hook        : {p.get('hook', '')}",
            f"Cliffhanger Cut  : {p.get('cliffhanger', '')}",
            f"Why It Works     : {p.get('why_it_works', '')}",
        ]
    )

    judge_v = p.get("judge_verdict") or {}
    if judge_v:
        lines.append(
            f"LLM Judge ({judge_v.get('judge_provider', 'LLM')}): "
            f"{judge_v.get('judge_score', p.get('total_score'))}/100 — {judge_v.get('verdict', '')}"
        )

    excerpts = p.get("script_excerpt", [])
    if excerpts:
        lines.append("")
        lines.append("SCRIPT EXCERPT IN CUT WINDOW:")
        for b in excerpts:
            ts = f"[{b.get('start', '')} - {b.get('end', '')}]"
            if b.get("type") == "DIALOGUE":
                tone = f" ({b.get('tone')})" if b.get("tone") else ""
                lines.append(f"  {ts} {b.get('speaker', 'SPEAKER')}{tone}: \"{b.get('content', '')}\"")
            else:
                lines.append(f"  {ts} [{b.get('type', 'ACTION')}] {b.get('content', '')}")

    lines.append("")
    return "\n".join(lines)


def format_stitched_promo_txt(s: Dict[str, Any], idx: int = 1, show_title: str = "") -> str:
    """Formats a multi-segment stitched/intercut trailer as an editor-ready plain-text cut sheet."""
    segments = s.get("segments") or []
    unique_eps = sorted({int(seg.get("episode", 1)) for seg in segments})
    ep_summary = ", ".join(f"Episode {e}" for e in unique_eps) if unique_eps else "N/A"
    lines = [
        "=" * 72,
        f"INTERCUT TRAILER #{idx}: {s.get('title', 'Stitched Promo')}",
        "=" * 72,
    ]
    if show_title:
        lines.append(f"Project / Show   : {show_title}")
    lines.extend(
        [
            f"Source Episode(s): {ep_summary}",
            f"Intercut         : Yes — {s.get('format', 'Multi-Segment')} ({len(segments)} segments)",
            f"Total Duration   : {s.get('total_duration_seconds', 0)}s",
            f"Score            : {s.get('total_score', 0)}/100",
            f"Marketing Tier   : {s.get('marketing_tier', '')}",
            "",
            "INTERCUT SEGMENTS (IN PLAYBACK ORDER):",
        ]
    )
    for seg in segments:
        lines.append(
            f"  Segment {seg.get('segment_index', '?')}: Episode {seg.get('episode', '?')} | "
            f"{seg.get('start_time', '')} -> {seg.get('end_time', '')} ({seg.get('duration_seconds', 0)}s)"
        )
        if seg.get("beat_description"):
            lines.append(f"    Beat: {seg['beat_description']}")

    lines.extend(
        [
            "",
            f"0-3s Hook        : {s.get('hook', '')}",
            f"Cliffhanger Cut  : {s.get('cliffhanger', '')}",
            f"Why It Works     : {s.get('why_it_works', '')}",
            "",
        ]
    )
    return "\n".join(lines)


def build_promos_txt_report(bundle: Dict[str, Any]) -> str:
    """Builds a complete plain-text promo report covering all ranked cuts and intercut trailers."""
    title = bundle.get("title", "Promo Export")
    promos = bundle.get("promos", [])
    stitched = bundle.get("stitched_promos", [])
    header = [
        f"KUKU PROMO STUDIO — PROMO CUT SHEETS",
        f"Project          : {title}",
        f"Episodes         : {bundle.get('episode_count', 0)}",
        f"Detected Promos  : {len(promos)}",
        f"Intercut Trailers: {len(stitched)}",
        f"Detection Mode   : {bundle.get('detection_label', '')}",
        f"Created          : {bundle.get('created_at', '')}",
        "",
    ]
    sections = ["\n".join(header)]

    if stitched:
        sections.append("#" * 72 + "\nMULTI-SEGMENT INTERCUT TRAILERS\n" + "#" * 72 + "\n")
        for idx, s in enumerate(stitched, 1):
            sections.append(format_stitched_promo_txt(s, idx=idx, show_title=title))

    if promos:
        sections.append("#" * 72 + "\nRANKED PROMO CUTS\n" + "#" * 72 + "\n")
        for p in promos:
            sections.append(format_single_promo_txt(p, show_title=title))

    return "\n".join(sections)


def build_promos_txt_zip(bundle: Dict[str, Any]) -> bytes:
    """Packages every promo and intercut trailer as separate .txt files inside a ZIP archive."""
    title = bundle.get("title", "Promo Export")
    promos = bundle.get("promos", [])
    stitched = bundle.get("stitched_promos", [])

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("00_ALL_PROMOS_SUMMARY.txt", build_promos_txt_report(bundle))
        for idx, p in enumerate(promos, 1):
            rank = int(p.get("rank", idx))
            ep = int(p.get("episode", 1))
            fname = f"promo_rank{rank:02d}_ep{ep:02d}.txt"
            zf.writestr(fname, format_single_promo_txt(p, show_title=title))
        for idx, s in enumerate(stitched, 1):
            slug = _safe_slug(s.get("title", f"intercut_{idx}"))
            fname = f"intercut_{idx:02d}_{slug}.txt"
            zf.writestr(fname, format_stitched_promo_txt(s, idx=idx, show_title=title))
    return buf.getvalue()


def build_export_artifacts(bundle: Dict[str, Any]) -> Dict[str, str]:
    """Generates Master JSON, Ranked CSV, FFmpeg script, Premiere markers, and plain-text cut sheets."""
    promos = bundle.get("promos", [])
    master_payload = {
        "show_title": bundle.get("title", "Promo Export"),
        "total_episodes_processed": bundle.get("episode_count", 0),
        "total_promos_extracted": len(promos),
        "detection_label": bundle.get("detection_label", ""),
        "promos": promos,
        "multi_segment_stitched_promos": bundle.get("stitched_promos", []),
    }
    json_str = json.dumps(master_payload, indent=2)

    csv_buf = io.StringIO()
    writer = csv.writer(csv_buf)
    writer.writerow([
        "Rank", "Episode", "Start Time", "End Time", "Duration (s)",
        "Marketing Tier", "Score (0-100)", "Detection Method", "Hook", "Cliffhanger", "Why It Works",
    ])
    for p in promos:
        seg = (p.get("segments") or [{}])[0]
        writer.writerow([
            p.get("rank", 0),
            p.get("episode", 1),
            seg.get("start_time", "00:00.00"),
            seg.get("end_time", "00:30.00"),
            p.get("total_duration_seconds", 0),
            p.get("marketing_tier", ""),
            p.get("total_score", 0),
            p.get("detection_method", ""),
            p.get("hook", ""),
            p.get("cliffhanger", ""),
            p.get("why_it_works", ""),
        ])

    ffmpeg_str = generate_ffmpeg_commands(promos)

    edl_buf = io.StringIO()
    edl_writer = csv.writer(edl_buf)
    edl_writer.writerow([
        "Marker Name", "Description", "In Timecode", "Out Timecode",
        "Duration (s)", "Rank", "Marketing Tier", "Clip Name",
    ])
    for p in promos:
        seg = (p.get("segments") or [{}])[0]
        edl_writer.writerow([
            f"Promo_Rank_{p.get('rank', 0):02d}_Ep{p.get('episode', 0):02d}",
            f"Hook: {p.get('hook', '')} | Cliffhanger: {p.get('cliffhanger', '')}",
            f"00:{seg.get('start_time', '00:00.00')}:00",
            f"00:{seg.get('end_time', '00:30.00')}:00",
            p.get("total_duration_seconds", 0),
            p.get("rank", 0),
            p.get("marketing_tier", ""),
            f"Episode_{p.get('episode', 0):02d}.mp4",
        ])

    ffmpeg_bat = re.sub(r"mkdir -p (\S+)", r"if not exist \1 mkdir \1", ffmpeg_str)
    txt_report = build_promos_txt_report(bundle)
    return {
        "json": json_str,
        "csv": csv_buf.getvalue(),
        "ffmpeg": ffmpeg_str,
        "ffmpeg_bat": ffmpeg_bat.replace("\n", "\r\n"),
        "edl": edl_buf.getvalue(),
        "txt": txt_report,
    }

