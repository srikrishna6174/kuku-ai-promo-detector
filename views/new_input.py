import streamlit as st

from src.input_manager import (
    parse_uploaded_files_as_separate_inputs,
    parse_uploaded_sources,
    process_episodes_into_bundle,
    save_bundle_to_disk,
)
from src.parser import parse_time_str
from views.ui_shared import navigate_to, render_ai_provider_controls, select_kw, stretch_kw

SAMPLE_THRILLER_SCRIPT = """EPISODE NUMBER: Episode 1
EPISODE LOGLINE: During an emergency board meeting, the whistleblowing CFO confronts the CEO with leaked offshore transfer records.

--- SCRIPT START ---

**CEO VANCE (Smooth, Threatening):**
Start: (00:00.00) | End: (00:04.20)
"You called an emergency vote at midnight, Maya. This better not waste my time."

**MAYA (Calm, Unyielding):**
Start: (00:04.50) | End: (00:08.60)
"Fourteen million dollars vanished from the pension fund three hours ago. Your signature is on every wire."

**SOUND FX:**
Start: (00:08.60) | End: (00:10.00)
Sharp metallic click as Maya locks the conference room doors electronically.

**CEO VANCE (Cold, Venomous):**
Start: (00:10.20) | End: (00:14.80)
"Careful, Maya. Nobody leaves this floor alive if they threaten my board seat."

**MAYA (Defiant):**
Start: (00:15.10) | End: (00:19.20)
"Too late. The federal prosecutor is already watching this livestream."

**CAMERA:**
Start: (00:19.20) | End: (00:22.40)
Close-up on Vance's phone lighting up with twenty simultaneous incoming alerts as sirens echo below.

**CEO VANCE (Panicked, Whispering):**
Start: (00:22.60) | End: (00:25.80)
"Who gave you my private encryption key...?"

**SOUND FX:**
Start: (00:25.80) | End: (00:27.50)
Low bass drone swells sharply, then hard cut to black.

--- SCRIPT END ---"""

SAMPLE_KUKU_SCRIPT = """EPISODE NUMBER: Episode 99
EPISODE LOGLINE: An unexpected visitor storms the wedding reception.

--- SCRIPT START ---

SCENE 01
Scene heading: INT. BALLROOM – NIGHT
Scene start: 00:00.00
Scene end: 01:30.00

**ARROGANT BILLIONAIRE (Venomous, Cold):**
Start: (00:01.00) | End: (00:04.20)
"You actually thought I was going to sign over the inheritance to a penniless maid?"

**LADY ELENA (Shocked, Trembling):**
Start: (00:04.50) | End: (00:06.80)
"We had a binding contract, Marcus!"

**ARROGANT BILLIONAIRE (Cruel, Mocking):**
Start: (00:07.10) | End: (00:09.50)
"Contracts are for equals. You are nothing."

**CAMERA:**
Start: (00:09.50) | End: (00:12.00)
Tight close-up as Marcus tears the paper in half and flings the shreds into Elena's face.

**LADY ELENA (Desperate, Tears falling):**
Start: (00:12.20) | End: (00:15.50)
"My mother needs that surgery tonight! You promised me!"

**ARROGANT BILLIONAIRE (Disgusted):**
Start: (00:16.00) | End: (00:19.00)
"Then I suppose she won't make it to sunrise."

**MYSTERIOUS COMMANDER (Low, Thunderous, Dangerous):**
Start: (00:22.00) | End: (00:26.50)
"Pick up those papers... and apologize to my wife."

**CAMERA:**
Start: (00:26.50) | End: (00:29.00)
Every guest freezes in horror as the city's most feared warlord steps through the shattered mahogany doors.

**ARROGANT BILLIONAIRE (Incredulous, Trembling):**
Start: (00:29.20) | End: (00:33.00)
"Y-Your wife?! She is an orphan!"

**MYSTERIOUS COMMANDER (Deadly, Uncompromising):**
Start: (00:33.50) | End: (00:37.00)
"She is the Duchess of Valmont. And your family dynasty ends in five minutes."

**SOUND FX:**
Start: (00:37.00) | End: (00:39.00)
Solemn low-pitched string drone swells to an ominous cliffhanger peak.

**CAMERA:**
Start: (00:39.00) | End: (00:40.00)
Cut to black.

--- SCRIPT END ---"""

SAMPLE_PLAIN_SCRIPT = """DETECTIVE REED: You told the precinct you never left Chicago last Tuesday.
SUSPECT CHEN: I didn't. Check the highway cameras if you don't believe me.
DETECTIVE REED: We did. Your car wasn't on the highway... because you were inside the vault at 2:14 AM!
SUSPECT CHEN: That's impossible. Nobody had the biometric override except—
DETECTIVE REED: Your brother. Who vanished the very same night.
[ACTION: Reed slides a blood-stained keycard across the metal table.]
SUSPECT CHEN: Where did you find that?! If you have his card, then he's already dead!
DETECTIVE REED: Not dead, Chen. Look behind the one-way glass..."""

SAMPLE_MAP = {
    "thriller": ("Corporate Thriller (Kuku Format)", "Corporate Thriller Ep 1", SAMPLE_THRILLER_SCRIPT),
    "ballroom": ("Ballroom Confrontation (Kuku Format)", "Ballroom Inheritance Ep 99", SAMPLE_KUKU_SCRIPT),
    "plain": ("Detective Interrogation (Plain Dialogue)", "Detective Interrogation", SAMPLE_PLAIN_SCRIPT),
}


def _on_sample_change():
    pick = st.session_state.get("studio_sample_pick", "none")
    if pick in SAMPLE_MAP:
        _, default_title, script_body = SAMPLE_MAP[pick]
        st.session_state["studio_textarea"] = script_body
        curr_title = st.session_state.get("studio_title_input", "").strip()
        sample_titles = {v[1] for v in SAMPLE_MAP.values()}
        if not curr_title or curr_title in sample_titles:
            st.session_state["studio_title_input"] = default_title
    elif pick == "clear":
        st.session_state["studio_textarea"] = ""
        curr_title = st.session_state.get("studio_title_input", "").strip()
        if curr_title in {v[1] for v in SAMPLE_MAP.values()}:
            st.session_state["studio_title_input"] = ""


def render_new_input_page():
    if st.session_state.pop("_clear_studio_textarea", False):
        st.session_state["studio_textarea"] = ""
        st.session_state["studio_title_input"] = ""
        st.session_state["studio_sample_pick"] = "none"

    st.markdown('<div class="page-title">Add New Project</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Upload episode scripts (.txt, .srt, .vtt, .zip) or paste text, then configure detection rules or AI models.</div>',
        unsafe_allow_html=True,
    )

    # ---- Step 1: Source & Metadata ----
    with st.container(border=True):
        st.markdown('<div class="section-heading">1. Script Source</div>', unsafe_allow_html=True)
        col_t, col_s, col_src = st.columns([2.0, 1.4, 1.3])
        with col_t:
            custom_title = st.text_input(
                "Project title (optional)",
                placeholder="e.g., Corporate Thriller Ep 1, Season 2...",
                key="studio_title_input",
            )
        with col_s:
            save_choice = st.selectbox(
                "After detection",
                ["Preview first (Session draft)", "Save to Project Library"],
                key="studio_save_choice",
                **select_kw(),
            )
        with col_src:
            input_source_mode = st.selectbox(
                "Source type",
                ["Upload Files or ZIP", "Paste Script Text"],
                key="studio_source_mode",
                **select_kw(),
            )

        uploaded_files = None
        multi_file_grouping = "combine"
        active_pasted_text = ""

        if input_source_mode == "Upload Files or ZIP":
            uploaded_files = st.file_uploader(
                "Drop .txt, .srt, .vtt, .md, or a season .zip archive",
                type=["txt", "srt", "vtt", "md", "zip"],
                accept_multiple_files=True,
                key="multi_txt_uploader",
            )
            if uploaded_files:
                file_names = [f.name for f in uploaded_files]
                st.success(
                    f"Selected {len(file_names)} file(s): {', '.join(file_names[:6])}{' ...' if len(file_names) > 6 else ''}"
                )
                non_zip = [f for f in uploaded_files if not f.name.lower().endswith(".zip")]
                if len(non_zip) > 1:
                    grp_choice = st.selectbox(
                        "Multiple files organization",
                        [
                            "Combine into 1 show (Episodes 1..N)",
                            "Create separate Project Library entry per file",
                        ],
                        key="studio_multi_grp",
                        **select_kw(),
                    )
                    multi_file_grouping = "separate" if grp_choice.startswith("Create separate") else "combine"
        else:
            sample_opts = ["none", "thriller", "ballroom", "plain", "clear"]
            sample_labels = {
                "none": "Load an example script (optional)...",
                "thriller": SAMPLE_MAP["thriller"][0],
                "ballroom": SAMPLE_MAP["ballroom"][0],
                "plain": SAMPLE_MAP["plain"][0],
                "clear": "Clear editor",
            }
            st.selectbox(
                "Example scripts",
                options=sample_opts,
                format_func=lambda k: sample_labels[k],
                key="studio_sample_pick",
                on_change=_on_sample_change,
                **select_kw(),
            )
            active_pasted_text = st.text_area(
                "Script or transcript text",
                height=210,
                placeholder="Supports Kuku screenplay format, SRT subtitles, [MM:SS] transcripts, or plain dialogue...",
                key="studio_textarea",
            )

    # ---- Step 2: Detection Configuration ----
    with st.container(border=True):
        st.markdown('<div class="section-heading">2. Detection Method</div>', unsafe_allow_html=True)

        m_col, d_col, k_col = st.columns([1.8, 1.5, 0.9])
        with m_col:
            mode_choice = st.selectbox(
                "Detection engine",
                [
                    "Rule-Based Cliffhanger Cuts (Fast, Offline)",
                    "AI Models (Multi-LLM + Failover + Judge)",
                    "Hybrid (Rule-Based + AI Models + Judge)",
                ],
                key="studio_mode_choice",
                **select_kw(),
            )
        if mode_choice.startswith("Rule-Based"):
            detection_mode = "manual"
        elif mode_choice.startswith("AI Models"):
            detection_mode = "llm"
        else:
            detection_mode = "both"

        with d_col:
            dur_range = st.slider("Duration window (sec)", 10, 90, (20, 60), key="studio_dur")
        with k_col:
            top_k = st.selectbox("Promos / ep", options=[1, 2, 3, 4, 5, 8, 10], index=1, key="studio_topk", **select_kw())

        custom_hook_kws, custom_cliff_kws = [], []
        custom_only, cliff_style = False, "any"
        pinned_cuts = []

        if detection_mode in ("manual", "both"):
            with st.expander("Rule Tuning & Optional Manual Cut", expanded=False):
                mk1, mk2 = st.columns(2)
                with mk1:
                    hook_kw_str = st.text_input(
                        "Custom hook words (comma-separated)",
                        placeholder="e.g., fired, secret, wire, betrayed",
                        key="studio_hook_kws",
                    )
                    custom_hook_kws = [x.strip() for x in hook_kw_str.split(",") if x.strip()]
                with mk2:
                    cliff_kw_str = st.text_input(
                        "Custom cliffhanger words (comma-separated)",
                        placeholder="e.g., cut to black, encryption key",
                        key="studio_cliff_kws",
                    )
                    custom_cliff_kws = [x.strip() for x in cliff_kw_str.split(",") if x.strip()]

                mc1, mc2 = st.columns([1.4, 1])
                with mc1:
                    style_label = st.selectbox(
                        "Cliffhanger ending preference",
                        [
                            "All Strong Cuts (Recommended)",
                            "Unresolved Question / Ellipsis (? / ... / —)",
                            "Action / Audio Sting Cut (CAMERA / SFX / MUSIC)",
                            "Prioritize Custom Cliffhanger Words",
                        ],
                        key="studio_cliff_style",
                        **select_kw(),
                    )
                    style_map = {
                        "All Strong Cuts (Recommended)": "any",
                        "Unresolved Question / Ellipsis (? / ... / —)": "question_ellipsis",
                        "Action / Audio Sting Cut (CAMERA / SFX / MUSIC)": "action_audio",
                        "Prioritize Custom Cliffhanger Words": "custom_only",
                    }
                    cliff_style = style_map[style_label]
                with mc2:
                    st.markdown("<div style='height: 26px;'></div>", unsafe_allow_html=True)
                    custom_only = st.checkbox("Use only custom keywords", value=False, key="studio_custom_only")

                st.markdown("**Pin an exact timestamp cut (optional)**")
                pc0, pc1, pc2, pc3 = st.columns([0.8, 1, 1, 2.2])
                with pc0:
                    pin_ep = st.number_input("Ep #", min_value=1, value=1, step=1, key="pin_ep_upload")
                with pc1:
                    pin_start_str = st.text_input("Start", value="", placeholder="00:04.50", key="pin_s_upload")
                with pc2:
                    pin_end_str = st.text_input("End", value="", placeholder="00:27.50", key="pin_e_upload")
                with pc3:
                    pin_cliff_note = st.text_input("Note", value="", placeholder="Why this cut works...", key="pin_n_upload")

                if pin_start_str.strip() and pin_end_str.strip():
                    try:
                        ps = parse_time_str(pin_start_str)
                        pe = parse_time_str(pin_end_str)
                        if pe > ps:
                            pinned_cuts.append(
                                {
                                    "episode": int(pin_ep),
                                    "start_time": ps,
                                    "end_time": pe,
                                    "cliffhanger_note": pin_cliff_note,
                                }
                            )
                        else:
                            st.warning("Manual cut End time must be greater than Start time.")
                    except ValueError:
                        st.warning("Could not parse manual cut times. Use MM:SS.SS or seconds.")

        llm_providers = []
        use_judge = False
        judge_provider_name = "auto"
        run_all_active_llms = True

        if detection_mode in ("llm", "both"):
            with st.expander("AI Providers & Judge (Gemini / OpenAI)", expanded=True):
                llm_providers, use_judge, judge_provider_name, run_all_active_llms = render_ai_provider_controls(
                    key_prefix="new_ai",
                    default_single_judge=(detection_mode == "both"),
                )

    # ---- Step 3: Action Row ----
    b1, b2, _ = st.columns([1.4, 1.0, 2.6])
    with b1:
        run_clicked = st.button("Run Promo Detection", type="primary", key="studio_run_btn", **stretch_kw(st.button))
    with b2:
        if st.button("Back to Home", key="studio_home_btn", **stretch_kw(st.button)):
            navigate_to("home")

    if run_clicked:
        has_files = bool(uploaded_files)
        has_paste = bool(active_pasted_text.strip())
        if not has_files and not has_paste:
            st.error("Please upload at least one file (.txt, .srt, .zip) or paste script text first.")
            return

        if detection_mode in ("llm", "both") and not llm_providers:
            st.error(
                "AI detection is selected, but no API key is configured. Add a session API key or switch to Rule-Based Cliffhanger Cuts."
            )
            return

        try:
            with st.spinner("Parsing input and finding top promos..."):
                auto_save = save_choice.startswith("Save to")

                if uploaded_files and len([f for f in uploaded_files if not f.name.lower().endswith(".zip")]) > 1 and multi_file_grouping == "separate":
                    batches = parse_uploaded_files_as_separate_inputs(uploaded_files)
                    if not batches:
                        st.error("Could not extract any script blocks from the uploaded files.")
                        return

                    first_id = None
                    for eps, batch_title in batches:
                        final_title = f"{custom_title.strip()} — {batch_title}" if custom_title.strip() else batch_title
                        bundle = process_episodes_into_bundle(
                            episodes=eps,
                            title=final_title,
                            detection_mode=detection_mode,
                            min_duration=float(dur_range[0]),
                            max_duration=float(dur_range[1]),
                            top_k_per_ep=int(top_k),
                            custom_hook_keywords=custom_hook_kws,
                            custom_cliffhanger_keywords=custom_cliff_kws,
                            custom_only=custom_only,
                            cliffhanger_style=cliff_style,
                            llm_providers=llm_providers,
                            use_judge=use_judge,
                            judge_provider_name=judge_provider_name,
                            run_all_active_llms=run_all_active_llms,
                            manual_cuts=pinned_cuts,
                            is_saved=auto_save,
                        )
                        if auto_save:
                            save_bundle_to_disk(bundle)
                        else:
                            st.session_state["unsaved_inputs"][bundle["id"]] = bundle
                        if first_id is None:
                            first_id = bundle["id"]

                    st.session_state["active_input_id"] = first_id
                    st.session_state["promos_page_num"] = 1
                    st.session_state["_clear_studio_textarea"] = True
                    navigate_to("library")
                else:
                    episodes, suggested_title = parse_uploaded_sources(
                        uploaded_files=uploaded_files,
                        pasted_text=active_pasted_text,
                    )
                    if not episodes:
                        st.error("Could not extract any dialogue or script blocks from the provided input.")
                        return

                    final_title = custom_title.strip() or suggested_title
                    bundle = process_episodes_into_bundle(
                        episodes=episodes,
                        title=final_title,
                        detection_mode=detection_mode,
                        min_duration=float(dur_range[0]),
                        max_duration=float(dur_range[1]),
                        top_k_per_ep=int(top_k),
                        custom_hook_keywords=custom_hook_kws,
                        custom_cliffhanger_keywords=custom_cliff_kws,
                        custom_only=custom_only,
                        cliffhanger_style=cliff_style,
                        llm_providers=llm_providers,
                        use_judge=use_judge,
                        judge_provider_name=judge_provider_name,
                        run_all_active_llms=run_all_active_llms,
                        manual_cuts=pinned_cuts,
                        is_saved=auto_save,
                    )

                    if auto_save:
                        save_bundle_to_disk(bundle)
                    else:
                        st.session_state["unsaved_inputs"][bundle["id"]] = bundle

                    st.session_state["active_input_id"] = bundle["id"]
                    st.session_state["promos_page_num"] = 1
                    st.session_state["_clear_studio_textarea"] = True
                    navigate_to("promos")
        except Exception as exc:
            st.error(f"Error processing input: {exc}")
