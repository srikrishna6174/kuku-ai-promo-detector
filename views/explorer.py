import glob
import os
import streamlit as st

from src.parser import parse_screenplay_file, parse_time_str
from views.ui_shared import (
    DATA_FOLDER,
    clean_html,
    format_source_label,
    navigate_to,
    render_active_header,
    render_promo_card,
    resolve_active_bundle,
    select_kw,
    stretch_kw,
)


def _promo_ranges_for_episode(ep_promos):
    ranges = []
    for p in ep_promos:
        seg = (p.get("segments") or [{}])[0]
        try:
            s_sec = float(p.get("start_seconds", parse_time_str(seg.get("start_time", "00:00.00"))))
            e_sec = float(p.get("end_seconds", parse_time_str(seg.get("end_time", "00:00.00"))))
            ranges.append((p.get("rank", "?"), s_sec, e_sec))
        except Exception:
            continue
    return ranges


def render_explorer_page():
    active_bundle = resolve_active_bundle()
    render_active_header(active_bundle, allow_switch=True)

    if active_bundle.get("is_empty"):
        if st.button("Open Project Library", icon=":material/folder_open:", key="exp_empty_lib"):
            navigate_to("library")
        return

    bundle_id = active_bundle["id"]
    promos_master = active_bundle.get("promos", [])

    st.markdown('<div class="page-title">Script Explorer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Inspect episode scripts beat-by-beat alongside the selected promo windows.</div>',
        unsafe_allow_html=True,
    )

    ep_dict = None
    ep_blocks = []
    fallback_excerpt_mode = False

    if active_bundle.get("is_builtin"):
        ep_files = active_bundle.get("ep_files") or (
            sorted(glob.glob(os.path.join(DATA_FOLDER, "*.txt"))) if os.path.exists(DATA_FOLDER) else []
        )
        total_eps = max(50, len(ep_files))
        c_ep, c_type, c_q = st.columns([1.2, 1.1, 1.7])
        with c_ep:
            selected_ep_num = st.selectbox(
                "Episode",
                range(1, total_eps + 1),
                format_func=lambda x: f"Episode {x:02d}",
                key=f"exp_ep_{bundle_id}",
                **select_kw(),
            )
        with c_type:
            block_filter = st.selectbox(
                "Block type",
                ["All Blocks", "Promo Windows Only", "Dialogue Only", "Camera / Action / SFX"],
                key=f"exp_type_{bundle_id}",
                **select_kw(),
            )
        with c_q:
            script_filter = st.text_input(
                "Filter script",
                placeholder="Speaker or keyword...",
                key=f"exp_filter_{bundle_id}",
            )

        if ep_files and selected_ep_num <= len(ep_files):
            parsed_ep = parse_screenplay_file(ep_files[selected_ep_num - 1])
            ep_dict = parsed_ep.to_dict()
            ep_blocks = [b.to_dict() for b in parsed_ep.blocks]
        else:
            fallback_excerpt_mode = True
    else:
        episodes_list = active_bundle.get("episodes", [])
        if not episodes_list:
            st.info("No episode script details are available for this dataset.")
            return
        ep_map = {int(e["episode_number"]): e for e in episodes_list}
        c_ep, c_type, c_q = st.columns([1.2, 1.1, 1.7])
        with c_ep:
            selected_ep_num = st.selectbox(
                "Episode",
                sorted(ep_map.keys()),
                format_func=lambda x: f"Episode {x:02d}",
                key=f"exp_ep_{bundle_id}",
                **select_kw(),
            )
        with c_type:
            block_filter = st.selectbox(
                "Block type",
                ["All Blocks", "Promo Windows Only", "Dialogue Only", "Camera / Action / SFX"],
                key=f"exp_type_{bundle_id}",
                **select_kw(),
            )
        with c_q:
            script_filter = st.text_input(
                "Filter script",
                placeholder="Speaker or keyword...",
                key=f"exp_filter_{bundle_id}",
            )
        ep_dict = ep_map[selected_ep_num]
        ep_blocks = ep_dict.get("blocks", [])

    ep_promos = [p for p in promos_master if int(p.get("episode", 1)) == int(selected_ep_num)]

    if fallback_excerpt_mode:
        # Cloud deploy without confidential local script folder: build blocks from embedded promo excerpts
        seen = set()
        for p in ep_promos:
            for b in p.get("script_excerpt", []):
                key_t = (b.get("start"), b.get("end"), b.get("content"))
                if key_t in seen:
                    continue
                seen.add(key_t)
                ep_blocks.append(
                    {
                        "block_type": b.get("type", "DIALOGUE"),
                        "speaker": b.get("speaker"),
                        "tone": b.get("tone"),
                        "start_time": parse_time_str(b.get("start", "00:00")),
                        "end_time": parse_time_str(b.get("end", "00:00")),
                        "start_formatted": b.get("start", "00:00"),
                        "end_formatted": b.get("end", "00:00"),
                        "content": b.get("content", ""),
                    }
                )
        ep_blocks.sort(key=lambda x: (x.get("start_time", 0.0), x.get("end_time", 0.0)))
        ep_dict = {
            "total_duration_formatted": ep_blocks[-1]["end_formatted"] if ep_blocks else "00:00.00",
            "block_count": len(ep_blocks),
            "dialogue_count": len([b for b in ep_blocks if b.get("block_type") == "DIALOGUE"]),
            "source_format": "kuku_screenplay",
            "logline": "Showing embedded promo script excerpts (full raw scripts are local-only).",
            "continuity": "",
        }

    if ep_dict:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Runtime", ep_dict.get("total_duration_formatted", "00:00.00"))
        m2.metric("Script Blocks", ep_dict.get("block_count", len(ep_blocks)))
        m3.metric("Dialogue Turns", ep_dict.get("dialogue_count", 0))
        m4.metric("Format", format_source_label(ep_dict.get("source_format", "kuku_screenplay")))

        with st.container(border=True):
            if ep_dict.get("timestamps_estimated"):
                st.caption("Timestamps were automatically estimated from speaking pace (~2.4 words/sec).")
            st.markdown(f"**Logline:** {ep_dict.get('logline') or 'N/A'}")
            if ep_dict.get("continuity"):
                st.caption(f"**Continuity:** {ep_dict.get('continuity')}")

    promo_ranges = _promo_ranges_for_episode(ep_promos)
    col_promos, col_script = st.columns([1.05, 1.15])

    with col_promos:
        st.markdown(f'<div class="section-heading">Promos in Episode {selected_ep_num} ({len(ep_promos)})</div>', unsafe_allow_html=True)
        if not ep_promos:
            st.info("No promos selected for this episode.")
        show_t = active_bundle.get("title", "")
        for p in ep_promos:
            render_promo_card(p, key_prefix="explorer", show_title=show_t)

    with col_script:
        st.markdown(f'<div class="section-heading">Script Timeline ({len(ep_blocks)} blocks)</div>', unsafe_allow_html=True)
        with st.container(height=560, border=True):
            q = script_filter.strip().lower()
            shown = 0
            for b in ep_blocks:
                btype = b.get("block_type", "DIALOGUE")
                if block_filter == "Dialogue Only" and btype != "DIALOGUE":
                    continue
                if block_filter == "Camera / Action / SFX" and btype == "DIALOGUE":
                    continue

                spk = b.get("speaker") or ""
                content = b.get("content") or ""
                if q and (q not in spk.lower() and q not in content.lower()):
                    continue

                b_start = float(b.get("start_time", 0.0))
                b_end = float(b.get("end_time", 0.0))
                matched_ranks = [
                    r for (r, ps, pe) in promo_ranges if b_end > ps + 0.05 and b_start < pe - 0.05
                ]
                if block_filter == "Promo Windows Only" and not matched_ranks:
                    continue

                shown += 1

                row_cls = "script-line script-line-in-promo" if matched_ranks else "script-line"
                rank_tag = (
                    "".join(f'<span class="script-promo-tag">Rank #{clean_html(r)}</span>' for r in matched_ranks[:2])
                    if matched_ranks
                    else ""
                )
                ts_span = f'<span class="script-ts">[{clean_html(b.get("start_formatted"))}–{clean_html(b.get("end_formatted"))}]</span>'

                if btype == "DIALOGUE":
                    tone_txt = f" ({clean_html(b.get('tone'))})" if b.get("tone") else ""
                    body_html = f"<b>{clean_html(spk)}</b>{tone_txt}: &ldquo;{clean_html(content)}&rdquo;"
                else:
                    body_html = f"<i>[{clean_html(btype)}]</i> {clean_html(content)}"

                st.markdown(f'<div class="{row_cls}">{ts_span}{rank_tag}{body_html}</div>', unsafe_allow_html=True)

            if shown == 0:
                if block_filter == "Promo Windows Only" and not ep_promos:
                    st.caption("No promo windows in this episode. Switch Block type to All Blocks to read the full script.")
                else:
                    st.caption("No script blocks match your filter.")
