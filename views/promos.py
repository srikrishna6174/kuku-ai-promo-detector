import math
import pandas as pd
import streamlit as st

from src.input_manager import (
    add_rule_based_promos_to_bundle,
    build_promos_txt_zip,
    enhance_bundle_with_ai,
    format_stitched_promo_txt,
    pin_manual_cut_any_bundle,
)
from src.parser import parse_time_str
from views.ui_shared import (
    navigate_to,
    render_active_header,
    render_ai_provider_controls,
    render_promo_card,
    resolve_active_bundle,
    select_kw,
    stretch_kw,
)


def _short_ts(ts: str) -> str:
    """Shortens MM:SS.SS to MM:SS for compact KPI metrics."""
    txt = str(ts or "00:00").strip()
    return txt.split(".")[0] if "." in txt else txt


def _classify_promo_type(p: dict) -> str:
    """Groups promos into clean UI categories: manual_cut, ai, or rule."""
    method = str(p.get("detection_method", "")).lower()
    if "manual cut" in method:
        return "manual_cut"
    if (
        "llm" in method
        or "both" in method
        or "hybrid" in method
        or "judged" in method
        or bool(p.get("judge_verdict"))
    ):
        return "ai"
    return "rule"


def _render_promo_type_section(
    section_key: str,
    title: str,
    items: list,
    bundle_key: str,
    show_title: str,
    view_mode: str,
    default_expanded: bool = True,
):
    """Renders a collapsible section for one promo generation type with 10/page navigation and dedicated scrollbar."""
    page_size = 10
    total_items = len(items)
    total_pages = max(1, math.ceil(total_items / page_size))
    pg_state_key = f"pg_{bundle_key}_{section_key}"
    curr_page = max(1, min(total_pages, int(st.session_state.get(pg_state_key, 1))))
    st.session_state[pg_state_key] = curr_page

    start_i = (curr_page - 1) * page_size
    end_i = min(total_items, start_i + page_size)
    page_items = items[start_i:end_i]

    with st.expander(f"{title} ({total_items})", expanded=default_expanded):
        if total_pages > 1:
            info_col, prev_col, next_col = st.columns([3.0, 0.85, 0.85], vertical_alignment="center")
            with info_col:
                st.markdown(
                    f'<div style="font-size:0.84rem;color:#6B7280;">'
                    f'Showing <b style="color:#18181B;">{start_i + 1}–{end_i}</b> of '
                    f'<b style="color:#18181B;">{total_items}</b> promos (Page {curr_page} of {total_pages})</div>',
                    unsafe_allow_html=True,
                )
            with prev_col:
                if st.button("Prev", disabled=(curr_page <= 1), key=f"prev_{bundle_key}_{section_key}", **stretch_kw(st.button)):
                    st.session_state[pg_state_key] = curr_page - 1
                    st.rerun()
            with next_col:
                if st.button("Next", disabled=(curr_page >= total_pages), key=f"next_{bundle_key}_{section_key}", **stretch_kw(st.button)):
                    st.session_state[pg_state_key] = curr_page + 1
                    st.rerun()

        if view_mode == "Compact Table":
            rows = []
            for p in page_items:
                seg = (p.get("segments") or [{}])[0]
                rows.append(
                    {
                        "Rank": p.get("rank"),
                        "Ep": p.get("episode"),
                        "Start": seg.get("start_time", ""),
                        "End": seg.get("end_time", ""),
                        "Duration (s)": p.get("total_duration_seconds"),
                        "Tier": str(p.get("marketing_tier", "")).split(":")[0],
                        "Score": p.get("total_score"),
                        "Method": p.get("detection_method", ""),
                        "Hook": p.get("hook", ""),
                        "Cliffhanger": p.get("cliffhanger", ""),
                    }
                )
            st.dataframe(pd.DataFrame(rows), hide_index=True, **stretch_kw(st.dataframe))
        else:
            scroll_box = st.container(height=540, border=False) if len(page_items) > 2 else st.container(border=False)
            with scroll_box:
                for p in page_items:
                    render_promo_card(p, key_prefix=f"promos_{section_key}", show_title=show_title)


def render_promos_page():
    active_bundle = resolve_active_bundle()
    render_active_header(active_bundle, allow_switch=True)

    if active_bundle.get("is_empty"):
        c1, c2, _ = st.columns([1.3, 1.3, 2.4])
        with c1:
            if st.button("Add New Project", type="primary", icon=":material/add:", key="pr_empty_new", **stretch_kw(st.button)):
                navigate_to("new_input")
        with c2:
            if st.button("Open Project Library", icon=":material/folder_open:", key="pr_empty_lib", **stretch_kw(st.button)):
                navigate_to("library")
        return

    promos_master = active_bundle.get("promos", [])
    stitched_master = active_bundle.get("stitched_promos", [])
    telemetry = active_bundle.get("telemetry", {})

    if telemetry.get("failover_triggered"):
        failures = telemetry.get("provider_failures", [])
        succ = telemetry.get("providers_succeeded", [])
        fail_txt = "; ".join(f"{f['provider']}: {f['error'][:85]}" for f in failures[:3])
        if succ:
            st.warning(f"LLM Failover activated ({fail_txt}). Completed with {', '.join(succ)}.")
        else:
            st.error(f"All configured LLMs failed ({fail_txt}). Used universal rule-based fallback.")
    if telemetry.get("judge_used"):
        st.info(f"Ranked with LLM-as-a-Judge ({', '.join(telemetry.get('judge_providers', []))}).")

    # 4-metric KPI strip with compact, non-truncating values
    ep_count = active_bundle.get("episode_count", 0)
    top_pick_val, top_pick_delta, avg_dur_val = "None", None, "0.0s"
    if promos_master:
        top_p = promos_master[0]
        top_seg = (top_p.get("segments") or [{}])[0]
        s_short = _short_ts(top_seg.get("start_time", "00:00"))
        e_short = _short_ts(top_seg.get("end_time", "00:00"))
        top_pick_val = f"Ep {top_p.get('episode', 1)} · {s_short}–{e_short}"
        top_pick_delta = f"Score {top_p.get('total_score', 0)}/100"
        avg_dur = sum(float(p.get("total_duration_seconds", 0)) for p in promos_master) / len(promos_master)
        avg_dur_val = f"{avg_dur:.1f}s"

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Episodes", ep_count)
    k2.metric("Promos Found", len(promos_master))
    k3.metric("Top Pick", top_pick_val, top_pick_delta)
    k4.metric("Avg Duration", avg_dur_val)

    st.markdown("<div style='height: 0.45rem;'></div>", unsafe_allow_html=True)

    if not promos_master:
        st.warning("No promos matched the criteria for this project.")
    else:
        if stitched_master:
            with st.expander(f"Stitched Multi-Segment Trailers ({len(stitched_master)})", expanded=False):
                show_t = active_bundle.get("title", "")
                stitched_box = st.container(height=420, border=False) if len(stitched_master) > 1 else st.container(border=False)
                with stitched_box:
                    for s_idx, s in enumerate(stitched_master):
                        with st.container(border=True):
                            sh_l, sh_r = st.columns([3.2, 1.1], vertical_alignment="center")
                            with sh_l:
                                st.markdown(f"**{s['title']}**")
                                st.caption(
                                    f"Intercut · {s['format']} · {s['total_duration_seconds']}s · Score {s['total_score']}/100"
                                )
                            with sh_r:
                                st.download_button(
                                    "Download .txt",
                                    data=format_stitched_promo_txt(s, idx=s_idx + 1, show_title=show_t),
                                    file_name=f"intercut_{s_idx + 1:02d}.txt",
                                    mime="text/plain",
                                    icon=":material/download:",
                                    key=f"dl_stitch_{active_bundle['id']}_{s_idx}",
                                    **stretch_kw(st.download_button),
                                )
                            st.markdown(f"**Hook (0–3s):** {s['hook']}")
                            st.markdown(f"**Cliffhanger:** {s['cliffhanger']}")
                            st.markdown(f"**Why it works:** {s['why_it_works']}")
                            for seg in s["segments"]:
                                st.markdown(
                                    f"- **Segment {seg['segment_index']}** · Ep {seg['episode']} `[{seg['start_time']}–{seg['end_time']}]`: {seg['beat_description']}"
                                )

        # Organized Filter & View Toolbar (Non-editable Dropdowns)
        ep_options = sorted({int(p.get("episode", 1)) for p in promos_master})
        bundle_key = active_bundle["id"]

        with st.container(border=True):
            f1, f2, f3, f4 = st.columns([1.35, 0.95, 1.25, 1.45])
            with f1:
                tier_filter = st.selectbox(
                    "Funnel tier",
                    [
                        "All Tiers",
                        "Tier 1: Cold UA (Post First)",
                        "Tier 2: High-Engagement",
                        "Tier 3: Retargeting",
                    ],
                    key=f"pr_tier_{bundle_key}",
                    **select_kw(),
                )
            with f2:
                ep_choices = ["All"] + [str(e) for e in ep_options]
                ep_filter = st.selectbox(
                    "Episode",
                    ep_choices,
                    format_func=lambda x: "All Episodes" if x == "All" else f"Episode {x}",
                    key=f"pr_ep_{bundle_key}",
                    **select_kw(),
                )
            with f3:
                sort_by = st.selectbox(
                    "Sort by",
                    [
                        "Strategic Rank",
                        "Score (High to Low)",
                        "Shortest Duration",
                        "Longest Duration",
                        "Episode Order",
                    ],
                    key=f"pr_sort_{bundle_key}",
                    **select_kw(),
                )
            with f4:
                search_query = st.text_input(
                    "Search speaker or line",
                    placeholder="e.g., secret, Maya, Juliana...",
                    key=f"pr_search_{bundle_key}",
                )

            v1, v2, v3 = st.columns([1.2, 2.5, 1.3], vertical_alignment="bottom")
            with v1:
                view_mode = st.selectbox(
                    "Display mode",
                    ["Detailed Cards", "Compact Table"],
                    key=f"pr_view_{bundle_key}",
                    **select_kw(),
                )

        # Reset per-section pagination automatically whenever filter/sort changes
        sig_key = f"promos_filter_sig_{bundle_key}"
        filter_sig = (bundle_key, tier_filter, ep_filter, sort_by, search_query.strip())
        if st.session_state.get(sig_key) != filter_sig:
            st.session_state[sig_key] = filter_sig
            for sec_k in ("manual_cut", "ai", "rule"):
                st.session_state[f"pg_{bundle_key}_{sec_k}"] = 1

        filtered = list(promos_master)
        if "Tier 1" in tier_filter:
            filtered = [p for p in filtered if "Tier 1" in p.get("marketing_tier", "")]
        elif "Tier 2" in tier_filter:
            filtered = [p for p in filtered if "Tier 2" in p.get("marketing_tier", "")]
        elif "Tier 3" in tier_filter:
            filtered = [p for p in filtered if "Tier 3" in p.get("marketing_tier", "")]

        if ep_filter != "All":
            target_ep = int(ep_filter)
            filtered = [p for p in filtered if int(p.get("episode", 1)) == target_ep]

        if search_query.strip():
            q = search_query.strip().lower()
            filtered = [
                p
                for p in filtered
                if q in p.get("hook", "").lower()
                or q in p.get("cliffhanger", "").lower()
                or q in p.get("why_it_works", "").lower()
                or any(
                    q in (b.get("speaker") or "").lower() or q in b.get("content", "").lower()
                    for b in p.get("script_excerpt", [])
                )
            ]

        if sort_by == "Score (High to Low)":
            filtered = sorted(filtered, key=lambda x: x.get("total_score", 0), reverse=True)
        elif sort_by == "Shortest Duration":
            filtered = sorted(filtered, key=lambda x: x.get("total_duration_seconds", 0))
        elif sort_by == "Longest Duration":
            filtered = sorted(filtered, key=lambda x: x.get("total_duration_seconds", 0), reverse=True)
        elif sort_by == "Episode Order":
            filtered = sorted(
                filtered,
                key=lambda x: (
                    int(x.get("episode", 1)),
                    str((x.get("segments") or [{}])[0].get("start_time", "")),
                ),
            )

        total_items = len(filtered)
        with v2:
            if total_items > 0:
                st.markdown(
                    f'<div style="font-size:0.84rem;color:#6B7280;padding-bottom:8px;">'
                    f'<b style="color:#18181B;">{total_items}</b> matching promos grouped by generation type below</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    '<div style="font-size:0.84rem;color:#6B7280;padding-bottom:8px;">No promos match your filter.</div>',
                    unsafe_allow_html=True,
                )
        with v3:
            st.download_button(
                "Download All .txt (.zip)",
                data=build_promos_txt_zip(active_bundle),
                file_name=f"{bundle_key}_promos_txt.zip",
                mime="application/zip",
                icon=":material/download:",
                key=f"pr_dl_all_{bundle_key}",
                **stretch_kw(st.download_button),
            )

        if not filtered:
            st.info("No promos matched your current filter.")
        else:
            grouped = {"manual_cut": [], "ai": [], "rule": []}
            for p in filtered:
                grouped[_classify_promo_type(p)].append(p)

            show_t = active_bundle.get("title", "")
            section_specs = [
                ("manual_cut", "Manual Timestamp Cuts"),
                ("ai", "AI-Generated & Enhanced Promos"),
                ("rule", "Rule-Based Promos"),
            ]
            for sec_k, sec_title in section_specs:
                sec_items = grouped[sec_k]
                if sec_items:
                    _render_promo_type_section(
                        section_key=sec_k,
                        title=sec_title,
                        items=sec_items,
                        bundle_key=bundle_key,
                        show_title=show_t,
                        view_mode=view_mode,
                        default_expanded=True,
                    )

    # ---- Secondary Project Enhancements (AI Generation + Manual Cut) ----
    has_episode_sources = bool(active_bundle.get("episodes") or active_bundle.get("ep_files"))
    if has_episode_sources:
        bundle_key = active_bundle["id"]
        ep_nums = (
            [int(e.get("episode_number", 1)) for e in active_bundle["episodes"]]
            if active_bundle.get("episodes")
            else list(range(1, len(active_bundle.get("ep_files", [])) + 1))
        )

        st.markdown("<div style='height: 0.45rem;'></div>", unsafe_allow_html=True)
        with st.expander("Request AI-Generated Promos (Gemini / OpenAI)", expanded=False):
            st.caption(
                "Run AI promo generation or LLM-as-a-Judge refinement directly on this project without re-uploading scripts."
            )
            if active_bundle.get("is_builtin"):
                st.caption("Running AI on the built-in benchmark creates an AI-enhanced project copy so the baseline stays intact.")

            scope_opts = (
                ["All Episodes"]
                if len(ep_nums) <= 3
                else ["Pilots (Episodes 1–3)", "Top 5 Scoring Episodes", "Specific Episode", "All Episodes"]
            )
            ai_c1, ai_c2, ai_c3 = st.columns([1.3, 1.3, 0.9])
            with ai_c1:
                ai_scope = st.selectbox(
                    "Target episodes",
                    scope_opts,
                    key=f"pr_ai_scope_{bundle_key}",
                    **select_kw(),
                )
            with ai_c2:
                ai_action = st.selectbox(
                    "AI action",
                    [
                        "Add AI Promos + Keep Existing",
                        "Run AI Judge on Existing Promos",
                        "Replace Selected Episodes with AI",
                    ],
                    key=f"pr_ai_act_{bundle_key}",
                    **select_kw(),
                )
            with ai_c3:
                if ai_scope == "Specific Episode":
                    picked_ep = st.selectbox(
                        "Episode #",
                        ep_nums,
                        format_func=lambda x: f"Episode {x}",
                        key=f"pr_ai_ep_{bundle_key}",
                        **select_kw(),
                    )
                else:
                    picked_ep = ep_nums[0] if ep_nums else 1

            llm_providers, use_judge, judge_provider_name, run_all_active_llms = render_ai_provider_controls(
                key_prefix=f"pr_ai_{bundle_key}",
                default_single_judge=True,
            )

            if st.button("Generate AI Promos", type="primary", key=f"pr_ai_go_{bundle_key}"):
                if not llm_providers:
                    st.error("Please enable Gemini or OpenAI (or provide a session API key) first.")
                else:
                    if ai_scope == "Specific Episode":
                        target_eps = [int(picked_ep)]
                    elif ai_scope == "Pilots (Episodes 1–3)":
                        target_eps = [e for e in ep_nums if e in (1, 2, 3)] or ep_nums[:3]
                    elif ai_scope == "Top 5 Scoring Episodes":
                        seen_top = []
                        for p in promos_master:
                            ep_i = int(p.get("episode", 1))
                            if ep_i not in seen_top:
                                seen_top.append(ep_i)
                            if len(seen_top) >= 5:
                                break
                        target_eps = seen_top or ep_nums[:5]
                    else:
                        target_eps = ep_nums

                    act_code = (
                        "judge_only"
                        if ai_action.startswith("Run AI Judge")
                        else ("replace" if ai_action.startswith("Replace") else "merge")
                    )

                    prog = st.progress(0.0, text="Starting AI promo analysis...")
                    try:
                        def _on_prog(done: int, total: int, ep_n: int):
                            prog.progress(min(1.0, done / max(1, total)), text=f"Analyzing Episode {ep_n} ({done}/{total})...")

                        updated_bundle, tel = enhance_bundle_with_ai(
                            bundle=active_bundle,
                            llm_providers=llm_providers,
                            target_episodes=target_eps,
                            action=act_code,
                            use_judge=use_judge,
                            judge_provider_name=judge_provider_name,
                            run_all_active_llms=run_all_active_llms,
                            progress_cb=_on_prog,
                        )
                        prog.empty()
                        if not updated_bundle.get("is_saved") and not updated_bundle.get("is_builtin"):
                            st.session_state["unsaved_inputs"][updated_bundle["id"]] = updated_bundle
                        st.session_state["active_input_id"] = updated_bundle["id"]
                        for sec_k in ("manual_cut", "ai", "rule"):
                            st.session_state[f"pg_{updated_bundle['id']}_{sec_k}"] = 1
                        st.rerun()
                    except Exception as exc:
                        prog.empty()
                        st.error(f"AI promo generation failed: {exc}")

        has_rule_promos = any(_classify_promo_type(p) == "rule" for p in promos_master)
        if not has_rule_promos:
            with st.expander("Request Rule-Based Promos (Fast, Offline)", expanded=False):
                st.caption(
                    "Generate rule-based cliffhanger cuts alongside your AI promos without overwriting existing results."
                )
                if st.button("Generate Rule-Based Promos", key=f"pr_rule_go_{bundle_key}"):
                    try:
                        updated_rule_b, added_cnt = add_rule_based_promos_to_bundle(active_bundle)
                        if not updated_rule_b.get("is_saved") and not updated_rule_b.get("is_builtin"):
                            st.session_state["unsaved_inputs"][updated_rule_b["id"]] = updated_rule_b
                        st.session_state["active_input_id"] = updated_rule_b["id"]
                        st.success(f"Added {added_cnt} rule-based promo cut(s).")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Rule-based promo generation failed: {exc}")

        with st.expander("Pin a Manual Timestamp Cut", expanded=False):
            if active_bundle.get("is_builtin"):
                st.caption("Adding a manual cut on the built-in benchmark creates a working copy so the baseline stays intact.")
            mc1, mc2, mc3 = st.columns(3)
            with mc1:
                chosen_ep = st.selectbox("Episode", ep_nums, key=f"mc_ep_{bundle_key}", **select_kw())
            with mc2:
                mc_start = st.text_input("Start (MM:SS.SS or sec)", "00:00.00", key=f"mc_s_{bundle_key}")
            with mc3:
                mc_end = st.text_input("End (MM:SS.SS or sec)", "00:30.00", key=f"mc_e_{bundle_key}")
            mc_note = st.text_input("Cliffhanger note (optional)", "", key=f"mc_n_{bundle_key}")

            if st.button("Add Manual Cut", key=f"mc_btn_{bundle_key}"):
                try:
                    ok, msg, updated_mc_bundle = pin_manual_cut_any_bundle(
                        active_bundle,
                        episode_number=int(chosen_ep),
                        start_time=parse_time_str(mc_start),
                        end_time=parse_time_str(mc_end),
                        cliffhanger_note=mc_note,
                    )
                    if ok:
                        if not updated_mc_bundle.get("is_saved") and not updated_mc_bundle.get("is_builtin"):
                            st.session_state["unsaved_inputs"][updated_mc_bundle["id"]] = updated_mc_bundle
                        st.session_state["active_input_id"] = updated_mc_bundle["id"]
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                except ValueError:
                    st.error("Invalid time format. Use MM:SS.SS (e.g. 00:12.50) or seconds (e.g. 12.5).")
