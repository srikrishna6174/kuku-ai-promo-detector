---
title: Kuku Promo Detector
emoji: 🎬
colorFrom: red
colorTo: purple
sdk: streamlit
sdk_version: 1.40.0
app_file: app.py
pinned: false
---

# 🎬 Kuku AI Promo Finder — Vertical Microdrama Ad Detector

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://kuku-ai-promo-detector.streamlit.app)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An automated tool built for **Kuku** that parses vertical microdrama screenplays and pinpoints high-converting **20s–60s promo clips** for TikTok, Instagram Reels, and YouTube Shorts.

Tested across all **50 episodes** of *I Married a Broken Soldier. He was a Duke*.

---

## 📌 Executive Summary

Microdrama ads drive user acquisition by converting cold scrollers into app downloads. A winning promo must satisfy three non-negotiable criteria:
1. **The Hook (First 0–3s)**: Halts scrolling with immediate betrayal, slap, or shocking accusation.
2. **The Cliffhanger (Ending)**: Cuts off sharply at peak emotional tension without resolving it.
3. **Standalone Comprehension**: A cold viewer with zero context immediately grasps who the villain is and what is at stake.

This project delivers a **Two-Stage Hybrid Architecture** (Deterministic NLP + LLM Evaluator) that balances speed, cost-efficiency ($0 base run), and deep semantic reasoning.

---

## 🏗️ Architecture: Hybrid 2-Stage Pipeline

```
50 Episode Scripts (.txt)
         │
         ▼
[Stage 1: Deterministic Screenplay Parser & Windowing]
  • Extracts exact millisecond timestamps, dialogue lines, camera cues, and speaker tones
  • Anchors high-tension start beats (betrayal, slap, confrontation)
  • Slides strict 20s–60s candidate windows
         │
         ▼
[Stage 2: Scoring & Filtering Engine]
  • Hook Score (0–10): Evaluates first 3 seconds
  • Cliffhanger Score (0–10): Evaluates cut-off tension & punctuation
  • Standalone Coherence (0–10): Evaluates speaker balance & dialogue turns
         │
         ▼
[Stage 3: Strategic Marketing Ranker]
  • Tier 1 (Post First / Cold UA): Episodes 1–3 (Altar betrayal & Stranger's rescue)
  • Tier 2 (Post Second / High-Engagement): Mid-season revenge & identity reveals
  • Tier 3 (Retargeting): Dramatic mid-funnel cliffhangers
         │
         ▼
[Outputs & Web UI]
  • promos_master.json (Structured timestamps & rationale)
  • promos_ranked.csv (Spreadsheet for editing suites)
  • quality_audit_and_failures.json (Honest failure analysis)
  • Interactive Streamlit Dashboard
```

---

## 🏆 Top Recommended Promos (Campaign Rollout)

| Rank | Episode | Timestamps | Duration | Funnel Tier | Hook Summary | Cliffhanger Cut |
|:---:|:---:|:---:|:---:|:---:|:---|:---|
| **#1** | **Ep 3** | `00:25.90 - 00:56.20` | 30.3s | **Tier 1 (Post First)** | Matriarch: *"You have humiliated this family enough for one day."* | Cuts on Matriarch: *"Your father has chosen his family... and it isn't you."* |
| **#2** | **Ep 1** | `01:15.00 - 01:38.20` | 23.2s | **Tier 1 (Post First)** | Cruel Sister: *"Long enough to know he was never going to marry you."* | Cuts on Juliana rising in tearful disbelief: *"Embarrassed you?"* |
| **#3** | **Ep 1** | `00:11.30 - 00:43.10` | 31.8s | **Tier 1 (Post First)** | Matriarch blocks bride: *"You should turn around, Juliana."* | Cuts on bride realizing groom holds sister's hand: *"No..."* |
| **#4** | **Ep 2** | `00:00.00 - 00:32.40` | 32.4s | **Tier 1 (Post First)** | Groom at altar: *"I cannot marry you, Juliana."* | Cuts on Juliana pleading to silent father: *"Father..."* |
| **#5** | **Ep 3** | `01:09.90 - 01:40.80` | 30.9s | **Tier 1 (Post First)** | Mysterious stranger: *"Take your hands off her."* | Cuts on stranger staring down armed guards: *"I can."* |

---

## ⚖️ Quality Audit & Failure Modes ("Where does the tool pick badly?")

In accordance with Kuku's assignment philosophy (*"An honest partial solution beats an overstated complete one"*), we built an automated audit system (`src/quality_checker.py`) that evaluated all 100 discovered clips:

1. **Premature Cut Buffer (Video Editing Gap - 58% of clips)**:
   * **Issue**: The script cuts off the millisecond the dialogue line ends. In actual video editing, cutting without a 0.5s–1.0s buffer chops off the actor's facial reaction or dramatic audio sting.
   * **Mitigation**: The system flags premature cuts so human editors know to extend the cut to the next camera reaction shot.
2. **Off-Target Side Characters (32% of clips)**:
   * **Issue**: Minor squabbles between servants or peripheral nobles score high on vocal aggression (shouting, insult words), but lack user acquisition appeal because cold audiences do not care about non-protagonists.
   * **Mitigation**: Added protagonist weighting to prioritize Juliana, Gerald, Clarissa, and the Duke.
3. **Exposition Overload (Lore Dependency)**:
   * **Issue**: Clips that discuss estate contracts or past family alliances have high dialogue counts but fail on TikTok because they require 10 episodes of prior context.
4. **Visual-Only Ambiguity**:
   * **Issue**: Purely physical moments (silent staring, weapon draws) lack dialogue keywords, causing text heuristics to underestimate their virality.

---

## 🚀 Quick Start Guide

### 1. Installation
```bash
git clone https://github.com/srikrishna6174/kuku-ai-promo-detector.git
cd kuku-ai-promo-detector
pip install -r requirements.txt
```

### 2. Run the Detection Pipeline (CLI)
Scans all 50 episodes in under 2 seconds and exports all JSON/CSV outputs:
```bash
python run_detection.py
```

### 3. Launch the Interactive Dashboard
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📂 Deliverables Manifest

* `run_detection.py` — Complete automated pipeline runner.
* `app.py` — Full interactive Streamlit web dashboard.
* `src/parser.py` — Screenplay parser with timestamp extraction.
* `src/detector.py` — Hook, cliffhanger & coherence scoring engine.
* `src/ranker.py` — Strategic campaign rollout & marketing tier classifier.
* `src/quality_checker.py` — Automated quality auditor & failure mode reporter.
* `src/llm_refiner.py` — Plug-and-play LLM adapter (Gemini / OpenAI / Local).
* `outputs/promos_master.json` — Unedited master JSON output across all 50 episodes.
* `outputs/promos_ranked.csv` — Ranked spreadsheet for video editors.
* `outputs/quality_audit_and_failures.json` — Detailed failure mode metrics.
* `Solution_Document.pdf` — 2-page executive solution doc for submission.

