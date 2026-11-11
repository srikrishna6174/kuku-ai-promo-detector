from typing import List, Optional
from src.detector import PromoCandidate


def rank_promos(
    promos: List[PromoCandidate],
    total_episodes: Optional[int] = None,
) -> List[PromoCandidate]:
    """
    Ranks promos strategically across a season or single uploaded input:

    - Multi-episode seasons (6+ episodes): prioritizes pilot episodes (Ep 1-3) for
      cold acquisition, followed by high-engagement escalation and retargeting.
    - Short inputs / single episodes (1-5 episodes): ranks purely by composite or
      LLM-as-a-Judge score and distributes funnel tiers by relative strength.
    """
    if not promos:
        return []

    max_ep = max((p.episode_number for p in promos), default=1)
    effective_total_eps = total_episodes if total_episodes is not None else max_ep
    is_full_season = effective_total_eps >= 6 or max_ep >= 6

    def effective_score(p: PromoCandidate) -> float:
        if p.judge_verdict and isinstance(p.judge_verdict.get("judge_score"), (int, float)):
            return float(p.judge_verdict["judge_score"])
        return float(p.total_score)

    if is_full_season:
        def ranking_key(p: PromoCandidate):
            tier_boost = 0.0
            if p.episode_number in (1, 2, 3):
                tier_boost = 25.0
            elif p.episode_number <= 10:
                tier_boost = 10.0
            elif p.episode_number <= 25:
                tier_boost = 5.0
            return effective_score(p) + tier_boost

        sorted_promos = sorted(promos, key=ranking_key, reverse=True)
        for idx, p in enumerate(sorted_promos, 1):
            p.rank = idx
            if p.episode_number in (1, 2, 3):
                p.funnel_type = "Tier 1: Top-of-Funnel (Cold UA) - Post First"
            elif p.rank <= 15:
                p.funnel_type = "Tier 2: High-Engagement Escalation - Post Second"
            else:
                p.funnel_type = "Tier 3: Retargeting & Cliffhanger Drive - Post Third"
        return sorted_promos

    sorted_promos = sorted(promos, key=effective_score, reverse=True)
    n = len(sorted_promos)
    tier1_cutoff = max(1, round(n * 0.35))
    tier2_cutoff = max(tier1_cutoff, round(n * 0.70))

    for idx, p in enumerate(sorted_promos, 1):
        p.rank = idx
        if idx <= tier1_cutoff and effective_score(p) >= 65.0:
            p.funnel_type = "Tier 1: Top-of-Funnel (Cold UA) - Post First"
        elif idx <= tier2_cutoff:
            p.funnel_type = "Tier 2: High-Engagement Escalation - Post Second"
        else:
            p.funnel_type = "Tier 3: Retargeting & Cliffhanger Drive - Post Third"

    return sorted_promos
