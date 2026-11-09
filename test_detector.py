from src.parser import parse_screenplay_file
from src.detector import find_promos_for_episode
import glob

files = sorted(glob.glob('I Married a Broken Soldier. He was a Duke/*.txt'))[:5]
for f in files:
    ep = parse_screenplay_file(f)
    promos = find_promos_for_episode(ep, top_k=2)
    print(f"=== Episode {ep.ep_number} Promos ===")
    for p in promos:
        d = p.to_dict()
        print(f"[{d['start_time']} - {d['end_time']} ({d['duration_seconds']}s)] Score: {d['total_score']} (Hook: {d['hook_score']}, Cliff: {d['cliffhanger_score']})")
        print(f"  Hook: {d['hook']}")
        print(f"  Cliffhanger: {d['cliffhanger']}")
        print(f"  Why: {d['why_it_works']}\n")
