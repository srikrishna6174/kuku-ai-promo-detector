from typing import List, Dict, Any
from src.detector import PromoCandidate

def rank_promos(promos: List[PromoCandidate]) -> List[PromoCandidate]:
    """
    Ranks promos strategically across the entire season for marketing campaigns:
    
    Tier 1 (Post First / Cold Acquisition):
        Episodes 1-3. Zero lore required. Maximum shock value (altar betrayal,
        evil sister, handsome mysterious rescuer).
        Highest click-through to install.
        
    Tier 2 (Post Second / High-Engagement Revenge & Escalation):
        Mid-season peaks (Episodes 4-20) with high dialogue tension, power reversal,
        or identity reveal. Drives viral TikTok/Reels shares.
        
    Tier 3 (Post Third / Retargeting & Mid-Funnel Bingeing):
        Cliffhanger-dense clips from later episodes that re-activate viewers
        who dropped off.
    """
    def ranking_key(p: PromoCandidate):
        # Priority boost for pilot episodes (Ep 1-3)
        tier_boost = 0
        if p.episode_number in (1, 2, 3):
            tier_boost = 25.0
        elif p.episode_number <= 10:
            tier_boost = 10.0
        elif p.episode_number <= 25:
            tier_boost = 5.0
            
        return p.total_score + tier_boost

    sorted_promos = sorted(promos, key=ranking_key, reverse=True)
    
    # Assign ranks and tiers
    for idx, p in enumerate(sorted_promos, 1):
        p.rank = idx
        if p.episode_number in (1, 2, 3):
            p.funnel_type = "Tier 1: Top-of-Funnel (Cold UA) - Post First"
        elif p.rank <= 15:
            p.funnel_type = "Tier 2: High-Engagement Escalation - Post Second"
        else:
            p.funnel_type = "Tier 3: Retargeting & Cliffhanger Drive - Post Third"
            
    return sorted_promos
