---
title: Kuku Promo Detector
emoji: 🎬
colorFrom: red
colorTo: purple
sdk: streamlit
sdk_version: 1.67.0
app_file: app.py
pinned: false
---

# 🎬 Kuku Promo Studio — Vertical Microdrama Ad Detector

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://kuku-ai-promo-detector.streamlit.app)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An automated tool built for **Kuku** that parses vertical microdrama screenplays (`.txt`, `.srt`, `.vtt`, `.md`, `.zip`, or pasted text) and pinpoints high-converting **20s–60s promo cut points** for TikTok, Instagram Reels, and YouTube Shorts — strictly identifying moments and start/end timestamps without adding baked video edits, music, or overlays.

Verified across all **50 episodes** of *I Married a Broken Soldier. He was a Duke* as well as arbitrary user-uploaded shows.

---

## 📌 Executive Summary & App Workflow

Microdrama ads drive user acquisition by converting cold scrollers into app downloads. Every promo candidate is scored across three criteria:
1. **The Hook (First 0–3s):** Halts scrolling with immediate betrayal, physical shock, or high-tension confrontation.
2. **The Cliffhanger (End Cut):** Cuts sharply at an unresolved beat so viewers click to see what happens next.
3. **Standalone Comprehension:** Works for a cold viewer who has zero prior episode context.

### Interactive Studio Pages (Per-Project Scoped)
* **Home:** Simple launcher with quick **Add New Project** & **Project Library** cards plus an inline active project switcher for its workspaces.
* **New Input:** Upload single/multiple scripts or season `.zip` archives, or paste dialogue directly; run offline **Rule-Based Cuts**, **Gemini** (`gemini-3.8-flash`), **OpenAI** (`gpt-4o-mini`), or **Hybrid + LLM-as-a-Judge** with automatic failover.
* **Project Library:** Switch between projects, rename via the inline edit icon, or delete projects along with all of their promos.
* **Promos:** Per-project view featuring **Stitched Multi-Segment Trailers**, collapsible sections grouped by promo type (`Manual Timestamp Cuts`, `AI-Generated & Enhanced Promos`, `Rule-Based Promos` with 10/page navigation), **Pin a Manual Timestamp Cut**, rule-based additions for AI-first projects, and one-click `.txt` cut-sheet downloads (single promo or full `.zip`).
* **Script Explorer:** Read any episode beat-by-beat with detected promo time windows highlighted inline.
* **Quality Audit:** Automated failure-mode inspection (premature cut buffers, off-target peripheral cast, exposition overload, visual-only ambiguity).

---

## 🏗️ Architecture: Two-Stage Hybrid Pipeline

```
Episode Scripts (.txt, .srt, .vtt, .zip, or Pasted Dialogue)
         │
         ▼
[Stage 1: Deterministic Screenplay Parser & Windowing]
  • Extracts timestamps, dialogue lines, camera/SFX cues, and speaker tones
  • Slides strict 20s–60s candidate windows anchored on high-tension beats
  • Flags premature dialogue cut boundaries needing a +0.75s reaction buffer
         │
         ▼
[Stage 2: Scoring & Optional Multi-LLM / Judge Layer]
  • Hook (40%) + Cliffhanger Cut (35%) + Standalone Coherence (25%)
  • Optional Gemini & OpenAI refinement + LLM-as-a-Judge with auto failover
  • Curates multi-segment stitched trailers & manual timestamp pins
         │
         ▼
[Stage 3: Strategic Campaign Ranker & Quality Audit]
  • Tier 1 (Post First / Cold UA): Episodes 1–3
  • Tier 2 (Post Second / Escalation): Mid-season reveals
  • Tier 3 (Post Third / Retargeting): Late-season cliffhangers
         │
         ▼
[Outputs & Cut Sheets]
  • outputs/promos/        -> promos_master.json, promos_ranked.csv, promos_report.txt, individual_promo_txt/, intercut_trailers/
  • outputs/quality_audit/ -> quality_audit_and_failures.json
  • outputs/editor_exports/-> cut_promos.sh (.bat), premiere_markers.csv
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

### 1. Installation & Optional AI Keys
```bash
git clone https://github.com/srikrishna6174/kuku-ai-promo-detector.git
cd kuku-ai-promo-detector
pip install -r requirements.txt
```
Offline rule-based promo detection works out of the box with zero API keys. To enable **Gemini** (`gemini-3.8-flash`) and/or **OpenAI** (`gpt-4o-mini`) generation and LLM-as-a-Judge refinement, copy `.env.example` to `.env` and fill in your keys (or paste them temporarily inside the UI):
```bash
cp .env.example .env
# Edit .env with GEMINI_API_KEY=... and/or OPENAI_API_KEY=...
```

### 2. Run the Detection Pipeline (CLI)
Scans all episodes and exports JSON, CSV, quality audit, FFmpeg, and Premiere marker outputs:
```bash
# Full season run (all 50 episodes)
python run_detection.py

# Run on a single episode
python run_detection.py --episode 3

# Run with Gemini or OpenAI API adapter
python run_detection.py --provider gemini
```

### 3. Launch the Interactive Studio
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

### 4. Run Automated Unit Tests (20/20 Passing)
```bash
python -m unittest test_pipeline.py test_universal_and_multi_llm.py -v
```

---

## 📂 Repository & Deliverables Manifest

* `app.py` — Streamlit multi-page entrypoint (`Home`, `New Input`, `Project Library`, `Promos`, `Script Explorer`, `Quality Audit`).
* `views/` — Clean UI modules (`home.py`, `new_input.py`, `library.py`, `promos.py`, `explorer.py`, `audit.py`, `ui_shared.py`).
* `run_detection.py` — CLI pipeline runner across single or multi-episode seasons.
* `solution_doc.md` & `Solution_Document.pdf` — Strictly 2-page executive solution document (generated via `generate_pdf.py`).
* `src/parser.py` — Multi-format screenplay parser (`.txt`, `.srt`, `.vtt`, `.zip`) with millisecond timestamp extraction.
* `src/detector.py` — Hook, cliffhanger, coherence, manual cut, and multi-segment intercut detector.
* `src/input_manager.py` — Project bundle persistence, post-AI manual/rule additions, and `.txt`/`.zip`/export builders.
* `src/ranker.py` — Strategic campaign rollout & marketing tier classifier.
* `src/quality_checker.py` — Automated quality auditor & failure-mode reporter.
* `src/llm_refiner.py` — Swappable Multi-LLM adapter (`Gemini` & `OpenAI`) with automatic failover & LLM-as-a-Judge.
* `src/export_utils.py` — Post-production FFmpeg & Premiere/Resolve marker generator.
* `test_pipeline.py` & `test_universal_and_multi_llm.py` — Automated unit test suite (**20/20** tests passing).
* `.env.example` — Template for optional `GEMINI_API_KEY` / `OPENAI_API_KEY` configuration.
* `outputs/promos/promos_master.json` — Master JSON output with embedded dialogue excerpts and 3 multi-segment trailers.
* `outputs/promos/promos_ranked.csv` — Ranked promo spreadsheet for editors.
* `outputs/promos/promos_report.txt` — Complete plain-text promo & intercut trailer cut-sheet report.
* `outputs/promos/individual_promo_txt/` — Individual `.txt` cut sheets for each ranked promo (`promo_rank001_ep03.txt` …).
* `outputs/promos/intercut_trailers/` — Individual `.txt` cut sheets for multi-segment intercut trailers.
* `outputs/quality_audit/quality_audit_and_failures.json` — Detailed failure-mode audit metrics.
* `outputs/editor_exports/cut_promos.sh` & `outputs/editor_exports/cut_promos.bat` — Stream-copy (`-c copy`) FFmpeg batch scripts (no overlays or edits).
* `outputs/editor_exports/premiere_markers.csv` — Timeline markers for Adobe Premiere Pro and DaVinci Resolve.

