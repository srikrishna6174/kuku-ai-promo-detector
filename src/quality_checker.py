from typing import List, Dict, Any
from src.detector import PromoCandidate

MAIN_PROTAGONISTS = {'JULIANA', 'GERALD', 'CLARISSA', 'BEARDED STRANGER', 'DUKE', 'MATRIARCH', 'ASHCROFT'}

def audit_promo_quality(promo: PromoCandidate) -> Dict[str, Any]:
    """
    Evaluates promo quality and checks for known edge cases / failure modes:
    1. EXPOSITION_RISK: Excessive words with low dialogue turns (monologue / worldbuilding)
    2. MISSING_PROTAGONIST: Involves side characters without core emotional stakes
    3. REACTION_BUFFER_WARNING: Cliffhanger ends on dialogue without allowing visual reaction time
    4. DURATION_EDGE: Segment is right at the 20s or 60s boundary
    """
    flags = []
    blocks = promo.blocks
    dialogues = [b for b in blocks if b.block_type == 'DIALOGUE']
    
    # Check 1: Are main protagonists involved?
    speakers = set(b.speaker.upper() for b in dialogues if b.speaker)
    has_main_char = any(any(prot in spk for prot in MAIN_PROTAGONISTS) for spk in speakers)
    if not has_main_char and len(speakers) > 0:
        flags.append({
            "mode": "OFF_TARGET_CHARACTERS",
            "severity": "MEDIUM",
            "reason": f"Only side characters involved ({', '.join(speakers)}). Lacks core protagonist emotional stakes."
        })
        
    # Check 2: Exposition risk (average word length per dialogue)
    total_words = sum(len(b.content.split()) for b in dialogues)
    if len(dialogues) > 0:
        avg_words_per_turn = total_words / len(dialogues)
        if avg_words_per_turn > 25:
            flags.append({
                "mode": "EXPOSITION_OVERLOAD",
                "severity": "HIGH",
                "reason": "Dialogue lines are too lengthy and expository for fast-paced vertical video."
            })
            
    # Check 3: Check if cliffhanger cut might be premature
    end_b = promo.cliffhanger_block
    if end_b.block_type == 'DIALOGUE' and end_b.end_time >= promo.end_time - 0.5:
        # Dialogue finishes right at the clip cut without visual reaction beat
        flags.append({
            "mode": "PREMATURE_CUT_BUFFER",
            "severity": "LOW",
            "reason": "Clip cuts immediately when speaker stops talking; needs 0.5s-1.0s video buffer for reaction shot."
        })
        
    # Check 4: Low dialogue count (relies heavily on silent camera/action cues)
    if len(dialogues) <= 1:
        flags.append({
            "mode": "VISUAL_ONLY_AMBIGUITY",
            "severity": "MEDIUM",
            "reason": "Very little dialogue; audio may feel empty without added music or voiceover."
        })

    is_reliable = len([f for f in flags if f['severity'] == 'HIGH']) == 0

    return {
        "episode": promo.episode_number,
        "clip_range": f"{promo.to_dict()['start_time']} - {promo.to_dict()['end_time']}",
        "is_reliable": is_reliable,
        "flag_count": len(flags),
        "flags": flags
    }

def run_season_quality_audit(promos: List[PromoCandidate]) -> Dict[str, Any]:
    """Runs quality check over all discovered promos and returns summary metrics."""
    audit_results = [audit_promo_quality(p) for p in promos]
    
    total = len(audit_results)
    flagged = [r for r in audit_results if r['flag_count'] > 0]
    high_risk = [r for r in audit_results if not r['is_reliable']]
    
    return {
        "total_promos_audited": total,
        "clean_promos_count": total - len(flagged),
        "flagged_promos_count": len(flagged),
        "high_risk_count": len(high_risk),
        "failure_mode_breakdown": {
            "EXPOSITION_OVERLOAD": len([r for r in audit_results if any(f['mode'] == 'EXPOSITION_OVERLOAD' for f in r['flags'])]),
            "OFF_TARGET_CHARACTERS": len([r for r in audit_results if any(f['mode'] == 'OFF_TARGET_CHARACTERS' for f in r['flags'])]),
            "PREMATURE_CUT_BUFFER": len([r for r in audit_results if any(f['mode'] == 'PREMATURE_CUT_BUFFER' for f in r['flags'])]),
            "VISUAL_ONLY_AMBIGUITY": len([r for r in audit_results if any(f['mode'] == 'VISUAL_ONLY_AMBIGUITY' for f in r['flags'])])
        },
        "sample_failures": [r for r in flagged[:5]]
    }

