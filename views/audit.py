from collections import Counter
from typing import Any, Dict, List
import pandas as pd
import streamlit as st

from src.parser import parse_time_str
from views.ui_shared import clean_html, render_active_header, resolve_active_bundle, select_kw, stretch_kw

MODE_LABELS = {
    "PREMATURE_CUT_BUFFER": "Premature Cut Buffer",
    "OFF_TARGET_CHARACTERS": "Off-Target Characters",
    "EXPOSITION_OVERLOAD": "Exposition Overload",
    "VISUAL_ONLY_AMBIGUITY": "Visual-Only Ambiguity",
}


def _reconstruct_flagged_from_promos(promos: List[Dict[str, Any]], lead_cast: List[str]) -> List[Dict[str, Any]]:
    """Builds structured flagged rows from embedded script excerpts when full flagged_details aren't stored."""
    prots = {c.upper() for c in lead_cast}
    if not prots and promos:
        counts: Counter = Counter()
        for p in promos:
            for b in p.get("script_excerpt", []):
                if b.get("type") == "DIALOGUE" and b.get("speaker"):
                    spk = b["speaker"].strip().upper()
                    if spk not in ("SPEAKER", "NARRATOR", "VOICEOVER", "VO"):
                        counts[spk] += 1
        prots = {s for s, _ in counts.most_common(5)}

    rows: List[Dict[str, Any]] = []
    for p in promos:
        ex = p.get("script_excerpt", [])
        if not ex:
            continue
        seg = (p.get("segments") or [{}])[0]
        start_s = seg.get("start_time", "00:00.00")
        end_s = seg.get("end_time", "00:00.00")
        dialogues = [b for b in ex if b.get("type") == "DIALOGUE"]
        flags = []

        speakers = {str(b.get("speaker") or "").upper() for b in dialogues if b.get("speaker")}
        if len(prots) >= 2 and speakers:
            has_lead = any(any(pr in s or s in pr for pr in prots) for s in speakers)
            if not has_lead:
                flags.append(
                    {
                        "mode": "OFF_TARGET_CHARACTERS",
                        "severity": "MEDIUM",
                        "reason": f"Only peripheral speakers involved ({', '.join(sorted(speakers))}).",
                    }
                )

        if dialogues:
            avg_words = sum(len(str(b.get("content") or "").split()) for b in dialogues) / len(dialogues)
            if avg_words > 25:
                flags.append(
                    {
                        "mode": "EXPOSITION_OVERLOAD",
                        "severity": "HIGH",
                        "reason": f"Dialogue averages {avg_words:.1f} words/turn (>25), risking scroll drop-off.",
                    }
                )

        try:
            seg_end_sec = parse_time_str(end_s)
            last_b = ex[-1]
            last_end_sec = parse_time_str(last_b.get("end", end_s))
            if last_b.get("type") == "DIALOGUE" and last_end_sec >= seg_end_sec - 0.5:
                flags.append(
                    {
                        "mode": "PREMATURE_CUT_BUFFER",
                        "severity": "LOW",
                        "reason": "Clip ends immediately on dialogue; add 0.5s–1.0s reaction buffer.",
                    }
                )
        except Exception:
            pass

        if len(dialogues) <= 1:
            flags.append(
                {
                    "mode": "VISUAL_ONLY_AMBIGUITY",
                    "severity": "MEDIUM",
                    "reason": "Very little dialogue (<=1 line); relies on visual cues or added audio.",
                }
            )

        if flags:
            rows.append(
                {
                    "rank": p.get("rank"),
                    "episode": p.get("episode"),
                    "clip_range": f"{start_s} - {end_s}",
                    "flags": flags,
                }
            )
    return rows


def render_audit_page():
    active_bundle = resolve_active_bundle()
    render_active_header(active_bundle, allow_switch=True)

    if active_bundle.get("is_empty"):
        return

    bundle_id = active_bundle["id"]
    promos_master = active_bundle.get("promos", [])
    audit_report = active_bundle.get("audit_report", {})

    st.markdown('<div class="page-title">Quality Audit & Failure Modes</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Automated checks highlighting where clips may need editor adjustments or context review.</div>',
        unsafe_allow_html=True,
    )

    inferred_cast = audit_report.get("inferred_protagonists", [])
    if inferred_cast:
        cast_pills = " ".join(f'<span class="pill pill-mode">{clean_html(c)}</span>' for c in inferred_cast)
        st.markdown(
            f'<div style="margin-bottom: 0.75rem; font-size: 0.86rem; color: #52525B;">'
            f'<b style="color:#18181B; margin-right:6px;">Detected Lead Cast:</b>{cast_pills}</div>',
            unsafe_allow_html=True,
        )

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Promos Audited", audit_report.get("total_promos_audited", len(promos_master)))
    q2.metric("Clean Promos", audit_report.get("clean_promos_count", 0))
    q3.metric("Flagged for Review", audit_report.get("flagged_promos_count", 0))
    q4.metric("High-Risk Flags", audit_report.get("high_risk_count", 0))

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    breakdown = audit_report.get("failure_mode_breakdown", {})

    cards_meta = [
        (
            "1. Premature Cut Buffer",
            breakdown.get("PREMATURE_CUT_BUFFER", 0),
            "Low",
            "pill-mode",
            "Clip ends immediately as dialogue finishes without a 0.5s–1.0s reaction buffer. Extend the out-point onto the next visual reaction beat.",
        ),
        (
            "2. Off-Target Characters",
            breakdown.get("OFF_TARGET_CHARACTERS", 0),
            "Medium",
            "pill-temp",
            "Speakers in this window are secondary characters rather than the primary lead cast, which can reduce cold-scroller empathy.",
        ),
        (
            "3. Exposition Overload",
            breakdown.get("EXPOSITION_OVERLOAD", 0),
            "High",
            "tag-hook",
            "Dialogue lines average over 25 words per turn, signaling heavy exposition that slows down short-form vertical pacing.",
        ),
        (
            "4. Visual-Only Ambiguity",
            breakdown.get("VISUAL_ONLY_AMBIGUITY", 0),
            "Medium",
            "pill-temp",
            "Clip contains one or fewer spoken lines and relies heavily on silent camera/action cues that may need music or voiceover.",
        ),
    ]

    c1, c2 = st.columns(2)
    for idx, (title, cnt, sev, sev_cls, desc) in enumerate(cards_meta):
        col = c1 if idx % 2 == 0 else c2
        with col:
            st.markdown(
                "".join(
                    [
                        '<div class="audit-card">',
                        '<div class="audit-card-head">',
                        f'<span class="audit-card-title">{clean_html(title)}</span>',
                        "<div>",
                        f'<span class="pill {sev_cls}">{clean_html(sev)}</span>',
                        f'<span class="pill badge-score" style="margin-left:6px;">{cnt} clip(s)</span>',
                        "</div>",
                        "</div>",
                        f'<div class="audit-card-desc">{clean_html(desc)}</div>',
                        "</div>",
                    ]
                ),
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 0.4rem;'></div>", unsafe_allow_html=True)

    raw_flagged = audit_report.get("flagged_details") or []
    is_reconstructed = False
    if not raw_flagged and promos_master:
        raw_flagged = _reconstruct_flagged_from_promos(promos_master, inferred_cast)
        is_reconstructed = True
    if not raw_flagged:
        raw_flagged = audit_report.get("sample_failures", [])

    if raw_flagged:
        exp_label = (
            "Inspect Flagged Clip Examples"
            if is_reconstructed
            else f"Inspect Flagged Clips ({len(raw_flagged)} clips)"
        )
        with st.expander(exp_label, expanded=False):
            if is_reconstructed:
                st.caption(
                    f"Showing {len(raw_flagged)} clips flagged by scanning the embedded script excerpts across the active promos."
                )
            mode_opts = ["ALL", "PREMATURE_CUT_BUFFER", "OFF_TARGET_CHARACTERS", "EXPOSITION_OVERLOAD", "VISUAL_ONLY_AMBIGUITY"]
            mode_names = {"ALL": "All Failure Modes", **MODE_LABELS}
            chosen_mode = st.selectbox(
                "Filter by failure mode",
                mode_opts,
                format_func=lambda k: mode_names.get(k, k),
                key=f"aud_mode_filter_{bundle_id}",
                **select_kw(),
            )

            table_rows = []
            for item in raw_flagged:
                for fl in item.get("flags", []):
                    m = fl.get("mode", "")
                    if chosen_mode != "ALL" and m != chosen_mode:
                        continue
                    table_rows.append(
                        {
                            "Episode": item.get("episode"),
                            "Time Range": item.get("clip_range"),
                            "Failure Mode": MODE_LABELS.get(m, m),
                            "Severity": fl.get("severity", "LOW"),
                            "Notes": fl.get("reason", ""),
                        }
                    )

            if table_rows:
                st.dataframe(pd.DataFrame(table_rows), hide_index=True, **stretch_kw(st.dataframe))
            else:
                st.caption("No flagged clips match this failure mode.")
    elif promos_master:
        st.success("All audited promos in this dataset passed without quality flags.")
