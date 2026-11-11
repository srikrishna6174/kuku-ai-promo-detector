from collections import Counter
from typing import List, Dict, Any, Optional, Set
from src.detector import PromoCandidate


def infer_main_protagonists(
    promos: Optional[List[PromoCandidate]] = None,
    episodes: Optional[List[Any]] = None,
    top_n: int = 5,
) -> Set[str]:
    """
    Dynamically infers lead characters from the speakers appearing most frequently
    across the supplied episodes or promo blocks.
    """
    counts: Counter = Counter()

    if episodes:
        for ep in episodes:
            for b in getattr(ep, "blocks", []):
                if getattr(b, "block_type", "") == "DIALOGUE" and getattr(b, "speaker", None):
                    spk = b.speaker.strip().upper()
                    if spk not in ("SPEAKER", "NARRATOR", "VOICEOVER", "VO"):
                        counts[spk] += 1

    if not counts and promos:
        for p in promos:
            for b in getattr(p, "blocks", []):
                if getattr(b, "block_type", "") == "DIALOGUE" and getattr(b, "speaker", None):
                    spk = b.speaker.strip().upper()
                    if spk not in ("SPEAKER", "NARRATOR", "VOICEOVER", "VO"):
                        counts[spk] += 1

    if not counts:
        return set()

    return {spk for spk, _ in counts.most_common(top_n)}


def audit_promo_quality(
    promo: PromoCandidate,
    protagonists: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Evaluates promo quality and checks for edge cases / failure modes:
    1. OFF_TARGET_CHARACTERS: Only minor/peripheral speakers when main cast was identified
    2. EXPOSITION_OVERLOAD: Excessive words per turn (monologue / worldbuilding)
    3. PREMATURE_CUT_BUFFER: Cliffhanger ends on dialogue without visual reaction buffer
    4. VISUAL_ONLY_AMBIGUITY: Very low dialogue count (silent action/camera cues)
    """
    flags = []
    blocks = promo.blocks
    dialogues = [b for b in blocks if b.block_type == "DIALOGUE"]

    # Check 1: Are lead characters involved (only when lead cast >= 2 distinct speakers exist)?
    speakers = set(b.speaker.upper() for b in dialogues if b.speaker)
    if protagonists and len(protagonists) >= 2 and len(speakers) > 0:
        has_main_char = any(
            any(prot in spk or spk in prot for prot in protagonists)
            for spk in speakers
        )
        if not has_main_char:
            flags.append({
                "mode": "OFF_TARGET_CHARACTERS",
                "severity": "MEDIUM",
                "reason": f"Only peripheral characters involved ({', '.join(sorted(speakers))}). Lacks lead character stakes.",
            })

    # Check 2: Exposition risk
    total_words = sum(len(b.content.split()) for b in dialogues)
    if len(dialogues) > 0:
        avg_words_per_turn = total_words / len(dialogues)
        if avg_words_per_turn > 25:
            flags.append({
                "mode": "EXPOSITION_OVERLOAD",
                "severity": "HIGH",
                "reason": "Dialogue lines are too lengthy and expository for fast-paced vertical video.",
            })

    # Check 3: Premature cut buffer
    end_b = promo.cliffhanger_block
    if end_b.block_type == "DIALOGUE" and end_b.end_time >= promo.end_time - 0.5:
        flags.append({
            "mode": "PREMATURE_CUT_BUFFER",
            "severity": "LOW",
            "reason": "Clip cuts immediately when speaker stops talking; needs 0.5s-1.0s video buffer for reaction shot.",
        })

    # Check 4: Low dialogue count
    if len(dialogues) <= 1:
        flags.append({
            "mode": "VISUAL_ONLY_AMBIGUITY",
            "severity": "MEDIUM",
            "reason": "Very little dialogue; audio may feel empty without added music or voiceover.",
        })

    is_reliable = len([f for f in flags if f["severity"] == "HIGH"]) == 0

    return {
        "episode": promo.episode_number,
        "clip_range": f"{promo.to_dict()['start_time']} - {promo.to_dict()['end_time']}",
        "is_reliable": is_reliable,
        "flag_count": len(flags),
        "flags": flags,
    }


def run_season_quality_audit(
    promos: List[PromoCandidate],
    protagonists: Optional[Set[str]] = None,
    episodes: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """Runs quality check over all discovered promos and returns summary metrics."""
    resolved_protagonists = protagonists if protagonists is not None else infer_main_protagonists(promos=promos, episodes=episodes)
    audit_results = [audit_promo_quality(p, protagonists=resolved_protagonists) for p in promos]

    total = len(audit_results)
    flagged = [r for r in audit_results if r["flag_count"] > 0]
    high_risk = [r for r in audit_results if not r["is_reliable"]]

    return {
        "total_promos_audited": total,
        "clean_promos_count": total - len(flagged),
        "flagged_promos_count": len(flagged),
        "high_risk_count": len(high_risk),
        "inferred_protagonists": sorted(resolved_protagonists),
        "failure_mode_breakdown": {
            "EXPOSITION_OVERLOAD": len([r for r in audit_results if any(f["mode"] == "EXPOSITION_OVERLOAD" for f in r["flags"])]),
            "OFF_TARGET_CHARACTERS": len([r for r in audit_results if any(f["mode"] == "OFF_TARGET_CHARACTERS" for f in r["flags"])]),
            "PREMATURE_CUT_BUFFER": len([r for r in audit_results if any(f["mode"] == "PREMATURE_CUT_BUFFER" for f in r["flags"])]),
            "VISUAL_ONLY_AMBIGUITY": len([r for r in audit_results if any(f["mode"] == "VISUAL_ONLY_AMBIGUITY" for f in r["flags"])]),
        },
        "sample_failures": [r for r in flagged[:5]],
        "flagged_details": [r for r in flagged],
    }
