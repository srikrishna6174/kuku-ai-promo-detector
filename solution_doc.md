# KUKU — AI GENERALIST ASSIGNMENT
## Problem 1: Find the Promos (Ads)
**Candidate:** Srikrishna Valepe | **Track:** AI Generalist Engineering

---

## 1. Problem Choice, Strategic Context & Framing

### Why Problem 1?
Microdramas are a high-velocity, organic acquisition format. The bottleneck for user acquisition (UA) on TikTok, Instagram Reels, and YouTube Shorts is manual video clipping: human editors spend hours per season scrubbing timelines to find 20–60s hooks. Automating this directly impacts top-of-funnel customer acquisition cost (CAC), publishing speed, and organic viral reach.

### Key Scoping Assumptions:
1. **Strict Duration Enforcement:** Clips must respect short-form algorithmic drop-off curves (optimal 25–45s; hard boundary 20–60s).
2. **Continuous & Multi-Segment Modes:** The primary focus is on single continuous dramatic beats to preserve raw emotional momentum without jarring cuts, accompanied by automated support for high-tempo 2-beat jumpcuts (e.g., Episode 1 Doorway Confrontation + Altar Betrayal; Episode 1 Humiliation + Episode 3 Hero Rescue).
3. **Zero-Lore Comprehension:** A top-of-funnel ad must be immediately understandable to a cold scroller within 3 seconds without knowing previous plotlines.

---

## 2. Technical Architecture: Two-Stage Hybrid Engine

To balance operational cost, latency, and nuanced creative reasoning at real-world scale, we rejected a naive "feed all 50 scripts into a closed LLM" approach. Instead, we architected a **Two-Stage Hybrid Pipeline**:

| Component | Deterministic Code / Simple Rules | Generative AI / LLM Layer |
| :--- | :--- | :--- |
| **Responsibilities** | • Screenplay parsing (`.txt`, `.srt`, `.vtt`, `.zip`) & regex extraction of millisecond timestamps.<br/>• Sliding window generation (20s–60s constraints, +0.75s reaction buffer).<br/>• Anchor detection: Dialogue starts, high-intensity tones (Cold, Furious, Desperate), confrontation keywords.<br/>• Mathematical scoring of 0–3s hook & final cliffhanger. | • Semantic tension assessment & context check.<br/>• Generates punchy social-media rationale ("Why it works") & LLM-as-a-Judge refinement.<br/>• Clickbait hook/cliffhanger framing & marketing angle identification.<br/>• Swappable API adapter (`Gemini` & `OpenAI` with automatic failover). |
| **Cost & Scale** | **$0.00 base cost**; runs in <2.0s across 50 episodes on standard CPU. | Only evaluates top filtered candidate windows (~2–4/ep) or selected episodes. Cost: **~$0.008 per show**. |

---

## 3. Scoring Rubric & Window Selection Logic

Candidate clips are evaluated on a composite 100-point scale across three weighted dimensions:
* **Hook Score (40%):** Evaluates the first 3.0 seconds. Looks for high-stakes disruption verbs (*"marry", "turn around", "betray", "enough"*), confrontational tones (*Venomous, Disgusted, Screaming*), or physical shock actions (*slap, tear, doors burst*).
* **Cliffhanger Score (35%):** Evaluates the final 3.0–5.0 seconds. Looks for unresolved interrogatives (*"?"*), interrupted statements (*"..."*), acoustic swells (*"ominous cliffhanger peak"*), or visual freeze/cut-to-black.
* **Standalone Coherence (25%):** Requires >= 2 distinct speakers in conflict and 4–10 dialogue turns. Penalizes monologue exposition.

---

## 4. Strategic Campaign Rollout: Which Promos to Post First & Why?

Ranking microdrama promos is not just about raw emotional score; it requires a **funnel-aligned publishing strategy**:

| Tier & Priority | Target Episodes | Strategic Rationale & Placement |
| :--- | :--- | :--- |
| **Tier 1: Post First**<br/>*(Cold User Acquisition)* | **Episodes 1 – 3**<br/>• Rank #1: Ep 3 (00:25–00:56)<br/>• Rank #2: Ep 1 (01:15–01:38) | **Zero-Lore Universality:** The wedding betrayal, sister stealing the groom, and mysterious hero's intervention require zero prior knowledge. Highest conversion from cold scroller to initial app install. |
| **Tier 2: Post Second**<br/>*(Viral Escalation & Shares)* | **Episodes 4 – 15**<br/>• Power reversal & public confrontations | **Power Reversal & Catharsis:** Juliana standing her ground and the Duke's true status emerging. Drives high comment velocity and algorithmic engagement on TikTok/Instagram. |
| **Tier 3: Post Third**<br/>*(Retargeting & Churn Prevention)* | **Episodes 16 – 50**<br/>• High-cliffhanger mid-season beats | **Binge Triggers:** Life-or-death and high-stakes ultimatums targeted at warm audiences who installed the app but stalled at Episode 5. |

---

## 5. Honest Quality Evaluation & Failure Modes ("Where does the tool pick badly?")

We ran an automated quality audit (`src/quality_checker.py`) across all 100 extracted promos from the 50 episodes. This surfaced **4 specific failure modes**:

1. **Premature Cut Buffer (58% of clips):** The script marks dialogue end at e.g. `00:32.40`. Cutting exactly at that timestamp clips the actor's stunned facial reaction or the sound sting.  
   *Mitigation:* Our parser adds an automated +0.75s visual reaction buffer.
2. **Off-Target Secondary Characters (32% of clips):** Heated shouting matches between maids or secondary aristocrats score high on acoustic/lexical aggression, but fail as ads because scrollers lack empathy for peripheral characters.  
   *Mitigation:* Implemented protagonist-weighting bonus.
3. **Lore & Exposition Overload:** Scenes debating estate ledgers or aristocratic lineage score high on dialogue balance but lack immediate visual/emotional peril.  
   *Mitigation:* Average-words-per-turn threshold flag (>25 words/turn flagged for review).
4. **Visual-Only Ambiguity:** Pure action moments (sword draws, silent glares) lack dialogue cues, leading text heuristics to underestimate them.  
   *Mitigation:* Multi-modal expansion roadmap.

---

## 6. AI Tools Used & One Place AI Got It Wrong

* **AI Tools Used:** Antigravity IDE coding agent for pipeline scaffolding, Streamlit UI iteration, and automated tests, paired with **Gemini** (`gemini-3.8-flash`) and **OpenAI** (`gpt-4o-mini`) API adapters for semantic promo selection and LLM-as-a-Judge scoring.
* **Where AI Got It Wrong:** When prompting LLMs directly over raw scripts, models frequently cut on the exact final spoken word (missing reaction shots), drifted past the strict 60s window limit, or hallucinated subtle timestamp offsets and secondary-character disputes. Similarly, initial AI-generated UI widgets allowed typing inside filter dropdowns and exposed unnecessary provider complexity. Wrapping the LLM behind deterministic timestamp parsing, strict 20–60s duration bounds, a +0.75s buffer check, and 20 automated unit tests fixed those gaps.

---

## 7. Production Scaling, Cost Analysis & Deliverables (Moments Only — No Overlays/Editing)

* **Cost at Scale:** Processing 20 new shows/week (1,000 episodes) using our hybrid approach costs **under $0.16/week** in API calls ($0 on base tier) and takes under 45 seconds of compute.
* **Human-in-the-Loop Workflow:** The tool acts as an AI Copilot for video editors—finding the exact promo start/end moments and manual cut pins without adding overlays, music, or baked video edits—reducing promo scouting from 4 hours to 10 minutes.
* **Deliverables Provided:**
  1. *Per-Project Streamlit Web App* (`Home`, `New Input`, `Project Library`, `Promos`, `Script Explorer`, `Quality Audit`) with live unseen-script upload and `.txt` promo cut sheets.
  2. *Unedited `outputs/` pack*: `promos_master.json`, `promos_ranked.csv`, and `quality_audit_and_failures.json` covering all 50 episodes.
  3. *Post-production cut exports*: FFmpeg cut scripts (`cut_promos.sh` / `.bat`) and timeline markers (`premiere_markers.csv`).
  4. *GitHub Repository* with 1-command reproducibility and **20/20** automated unit tests (`test_pipeline.py` & `test_universal_and_multi_llm.py`).

