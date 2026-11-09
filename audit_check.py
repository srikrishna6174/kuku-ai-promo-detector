import json
import os
import csv
import pypdf

def audit():
    print("=== JUDICIAL AUDIT OF SUBMISSION ARTIFACTS ===")
    
    # 1. Master JSON
    with open('outputs/promos_master.json', 'r', encoding='utf-8') as f:
        master = json.load(f)
    print(f"[✓] promos_master.json loaded. Episodes: {master['total_episodes_processed']}, Promos: {len(master['promos'])}, Stitched: {len(master.get('multi_segment_stitched_promos', []))}")
    
    # 2. Ranked CSV
    with open('outputs/promos_ranked.csv', 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
    print(f"[✓] promos_ranked.csv loaded. Header + {len(reader)-1} rows.")
    
    # 3. Quality audit
    with open('outputs/quality_audit_and_failures.json', 'r', encoding='utf-8') as f:
        qa = json.load(f)
    print(f"[✓] quality_audit.json loaded. Total audited: {qa['total_promos_audited']}, Flagged: {qa['flagged_promos_count']}")

    # 4. Solution PDF
    reader = pypdf.PdfReader('Solution_Document.pdf')
    print(f"[✓] Solution_Document.pdf loaded. Page count: {len(reader.pages)} (Must be strictly 2)")
    assert len(reader.pages) == 2, f"PDF page count is {len(reader.pages)}, must be 2!"
    
    # Check top 5 ranks
    print("\nTop 5 Promos:")
    for p in master['promos'][:5]:
        seg = p['segments'][0]
        print(f"  #{p['rank']} | Ep {p['episode']} [{seg['start_time']} - {seg['end_time']}] | Score: {p['total_score']} | Tier: {p['marketing_tier'].split(':')[0]}")
        print(f"     Hook: {p['hook'][:70]}")
        print(f"     Cliff: {p['cliffhanger'][:70]}")

if __name__ == "__main__":
    audit()

