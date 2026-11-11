import html
import inspect
import os
from typing import Any, Dict, List
import pandas as pd
import streamlit as st

from src.llm_refiner import LLMProviderConfig, PROVIDER_DEFAULTS, get_backend_provider_status
from src.input_manager import (
    BUILTIN_INPUT_ID,
    build_export_artifacts,
    build_promos_txt_zip,
    format_single_promo_txt,
    is_builtin_hidden,
    list_saved_inputs,
    load_builtin_bundle,
    load_saved_bundle,
    save_bundle_to_disk,
)

DATA_FOLDER = "I Married a Broken Soldier. He was a Duke"
OUTPUT_DIR = "outputs"

PAGE_REGISTRY: Dict[str, Any] = {}

FORMAT_LABELS = {
    "kuku_screenplay": "Screenplay",
    "srt_subtitles": "SRT / VTT",
    "timestamped_transcript": "Transcript",
    "plain_script_estimated": "Plain Text",
}


def stretch_kw(widget_fn) -> Dict[str, Any]:
    """Uses width='stretch' on newer Streamlit releases and falls back cleanly on older ones."""
    try:
        params = inspect.signature(widget_fn).parameters
        if "width" in params:
            return {"width": "stretch"}
    except Exception:
        pass
    return {"use_container_width": True}


def select_kw() -> Dict[str, Any]:
    """Makes dropdowns non-editable (pure select menu without text typing)."""
    try:
        params = inspect.signature(st.selectbox).parameters
        if "filter_mode" in params:
            return {"filter_mode": None}
    except Exception:
        pass
    return {}


def format_source_label(source_format: str) -> str:
    return FORMAT_LABELS.get(source_format, (source_format or "Script").replace("_", " ").title())


def clean_html(val: Any) -> str:
    return html.escape(" ".join(str(val or "").split()))


def navigate_to(page_key: str):
    """Switches cleanly to a registered st.Page object."""
    target = PAGE_REGISTRY.get(page_key)
    if target is not None:
        st.switch_page(target)


def apply_global_styles():
    css = """<style>
:root {
    --k-bg: #FAFAF8;
    --k-surface: #FFFFFF;
    --k-muted-surface: #F4F4F1;
    --k-border: #E5E7EB;
    --k-ink: #18181B;
    --k-ink-2: #3F3F46;
    --k-muted: #6B7280;
    --k-accent: #2B5B84;
}

.stApp {
    background-color: var(--k-bg);
    color: var(--k-ink);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
}

[data-testid="stHeader"] {
    background-color: rgba(250, 250, 248, 0.94);
    border-bottom: 1px solid var(--k-border);
    backdrop-filter: blur(6px);
}
[data-testid="stAppDeployButton"],
.stAppDeployButton {
    display: none !important;
}

[data-testid="stMainBlockContainer"] {
    padding-top: 5rem !important;
    padding-bottom: 2.5rem;
    max-width: 1240px;
}

[data-testid="stSidebar"] {
    background-color: #F3F3F0;
    border-right: 1px solid var(--k-border);
}

[data-testid="stSelectbox"] [data-baseweb="select"],
[data-testid="stSelectbox"] [data-baseweb="select"] * {
    cursor: pointer !important;
}
[data-testid="stSelectbox"] input {
    caret-color: transparent !important;
}

/* Crisp balanced metrics that never truncate mid-label */
[data-testid="stMetric"] {
    background-color: var(--k-surface);
    border: 1px solid var(--k-border);
    border-top: 3px solid #3B82F6;
    border-radius: 8px;
    padding: 0.72rem 0.9rem;
    min-height: 98px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
[data-testid="stMetricLabel"] {
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    color: var(--k-muted) !important;
    margin-bottom: 2px;
}
[data-testid="stMetricValue"] {
    font-size: 1.28rem !important;
    font-weight: 650 !important;
    color: var(--k-ink) !important;
    line-height: 1.3 !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    font-variant-numeric: tabular-nums;
}
[data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
    font-weight: 500 !important;
}

/* Clean page typography */
.page-title {
    font-size: 1.42rem;
    font-weight: 650;
    color: var(--k-ink);
    letter-spacing: -0.015em;
    line-height: 1.25;
    margin: 0 0 0.2rem 0;
}
.page-subtitle {
    font-size: 0.91rem;
    color: var(--k-muted);
    line-height: 1.45;
    margin: 0 0 0.95rem 0;
}
.section-heading {
    font-size: 1.04rem;
    font-weight: 600;
    color: var(--k-ink);
    margin: 0.3rem 0 0.55rem 0;
}

/* Slim light context bar */
.context-bar {
    background: linear-gradient(90deg, #FFFFFF 0%, #F8FAFC 100%);
    border: 1px solid #DBEAFE;
    border-left: 4px solid #2563EB;
    border-radius: 10px;
    padding: 0.75rem 1.05rem;
    margin-bottom: 0.95rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px 16px;
}
.context-title-row {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
}
.context-title {
    font-size: 1.06rem;
    font-weight: 650;
    color: var(--k-ink);
    margin: 0;
}
.context-meta {
    font-size: 0.84rem;
    color: var(--k-muted);
    font-variant-numeric: tabular-nums;
}

/* Soft human-friendly status & score pills */
.pill {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 999px;
    font-size: 0.74rem;
    font-weight: 600;
    line-height: 1.45;
    border: 1px solid transparent;
    vertical-align: middle;
}
.pill-builtin { background-color: #EFF6FF; color: #1E40AF; border-color: #DBEAFE; }
.pill-saved   { background-color: #ECFDF5; color: #065F46; border-color: #D1FAE5; }
.pill-temp    { background-color: #FFFBEB; color: #92400E; border-color: #FDE68A; }
.pill-mode    { background-color: #F4F4F5; color: #3F3F46; border-color: #E4E4E7; }
.pill-active  { background-color: #ECFDF5; color: #047857; border-color: #A7F3D0; }

/* Light editorial promo cards with subtle tier accents */
.promo-card {
    background-color: var(--k-surface);
    border: 1px solid var(--k-border);
    border-left: 4px solid #2563EB;
    border-radius: 8px;
    padding: 0.95rem 1.15rem;
    margin-bottom: 0.35rem;
    box-sizing: border-box;
    max-width: 100%;
    overflow-wrap: anywhere;
}
.promo-card-t1 { border-left-color: #10B981; }
.promo-card-t2 { border-left-color: #2563EB; }
.promo-card-t3 { border-left-color: #F59E0B; }
.promo-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 0.6rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #F1F1EE;
}
.promo-title {
    font-size: 0.99rem;
    font-weight: 650;
    color: var(--k-ink);
}
.promo-time {
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--k-muted);
    margin-left: 10px;
    font-variant-numeric: tabular-nums;
}
.promo-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
}
.promo-row {
    font-size: 0.91rem;
    color: var(--k-ink-2);
    line-height: 1.52;
    margin-bottom: 0.42rem;
    overflow-wrap: anywhere;
}
.promo-why {
    font-size: 0.86rem;
    color: var(--k-muted);
    margin-top: 0.45rem;
    line-height: 1.48;
    overflow-wrap: anywhere;
}
.promo-judge {
    font-size: 0.85rem;
    color: #78350F;
    background-color: #FFFBEB;
    border: 1px solid #FDE68A;
    border-radius: 6px;
    padding: 0.48rem 0.72rem;
    margin-top: 0.55rem;
    line-height: 1.45;
    overflow-wrap: anywhere;
}

.tag-hook {
    display: inline-block;
    background-color: #FFE4E6;
    color: #BE123C;
    border: 1px solid #FDA4AF;
    font-weight: 600;
    padding: 1px 8px;
    border-radius: 5px;
    font-size: 0.75rem;
    margin-right: 7px;
}
.tag-cliff {
    display: inline-block;
    background-color: #E0E7FF;
    color: #4338CA;
    border: 1px solid #A5B4FC;
    font-weight: 600;
    padding: 1px 8px;
    border-radius: 5px;
    font-size: 0.75rem;
    margin-right: 7px;
}
.badge-tier-1 { background-color: #D1FAE5; color: #047857; border: 1px solid #6EE7B7; }
.badge-tier-2 { background-color: #DBEAFE; color: #1D4ED8; border: 1px solid #93C5FD; }
.badge-tier-3 { background-color: #FEF3C7; color: #B45309; border: 1px solid #FCD34D; }
.badge-score  { background-color: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE; }
.badge-method { background-color: #F3F4F6; color: #374151; border: 1px solid #D1D5DB; }
.badge-judge  { background-color: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }

.promo-badge {
    font-weight: 600;
    padding: 2px 9px;
    border-radius: 6px;
    font-size: 0.75rem;
    display: inline-block;
    font-variant-numeric: tabular-nums;
}

/* Soft audit failure cards */
.audit-card {
    background-color: var(--k-surface);
    border: 1px solid var(--k-border);
    border-radius: 8px;
    padding: 0.9rem 1.05rem;
    margin-bottom: 0.65rem;
}
.audit-card-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
    margin-bottom: 0.38rem;
}
.audit-card-title {
    font-size: 0.97rem;
    font-weight: 650;
    color: var(--k-ink);
}
.audit-card-desc {
    font-size: 0.86rem;
    color: var(--k-muted);
    line-height: 1.48;
}

/* Clean expander surfaces */
[data-testid="stExpander"] details {
    background-color: var(--k-surface);
    border: 1px solid var(--k-border);
    border-radius: 8px;
}
[data-testid="stExpander"] summary p {
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: var(--k-ink-2) !important;
}

/* Script explorer highlight row */
.script-line {
    padding: 0.35rem 0.6rem;
    border-radius: 5px;
    margin-bottom: 0.25rem;
    font-size: 0.88rem;
    line-height: 1.48;
    color: var(--k-ink-2);
}
.script-line-in-promo {
    background-color: #F0F5FA;
    border-left: 3px solid var(--k-accent);
}
.script-ts {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 0.78rem;
    color: var(--k-muted);
    margin-right: 6px;
}
.script-promo-tag {
    display: inline-block;
    background-color: #DBEAFE;
    color: #1E40AF;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 0 6px;
    border-radius: 4px;
    margin-right: 6px;
}

/* Home explorer square launcher tiles */
.hub-tile-body {
    min-height: 158px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    padding: 0.25rem 0.1rem 0.65rem 0.1rem;
}
.hub-tile-top {
    margin-bottom: 0.55rem;
}
.hub-tile-step {
    display: inline-block;
    background-color: #EFF6FF;
    color: #1D4ED8;
    border: 1px solid #BFDBFE;
    font-size: 0.73rem;
    font-weight: 600;
    padding: 2px 9px;
    border-radius: 999px;
    letter-spacing: 0.01em;
}
.hub-step-0 { background-color: #DBEAFE; color: #1D4ED8; border-color: #93C5FD; }
.hub-step-1 { background-color: #CCFBF1; color: #0F766E; border-color: #5EEAD4; }
.hub-step-2 { background-color: #FFE4E6; color: #BE123C; border-color: #FDA4AF; }
.hub-step-3 { background-color: #E0E7FF; color: #4338CA; border-color: #A5B4FC; }
.hub-step-4 { background-color: #FEF3C7; color: #B45309; border-color: #FCD34D; }
.hub-step-5 { background-color: #D1FAE5; color: #047857; border-color: #6EE7B7; }
.hub-tile-title {
    font-size: 1.08rem;
    font-weight: 650;
    color: var(--k-ink);
    margin-bottom: 0.35rem;
    line-height: 1.3;
}
.hub-tile-desc {
    font-size: 0.88rem;
    color: var(--k-ink-2);
    line-height: 1.5;
    margin-bottom: 0.75rem;
}
.hub-tile-meta {
    margin-top: auto;
    font-size: 0.8rem;
    color: var(--k-muted);
    font-weight: 500;
}

/* Compact icon triggers for Project Library card edit/delete popovers */
[data-testid="stPopover"] button[kind="tertiary"] {
    padding: 0.12rem 0.28rem !important;
    min-height: 1.65rem !important;
    height: 1.65rem !important;
    min-width: 1.65rem !important;
    line-height: 1 !important;
    border-radius: 6px !important;
    color: #6B7280 !important;
    border: 1px solid transparent !important;
}
[data-testid="stPopover"] button[kind="tertiary"]:hover {
    background-color: #F3F4F6 !important;
    border-color: #E5E7EB !important;
    color: #18181B !important;
}
[data-testid="stPopover"] button[kind="tertiary"] [data-testid="stMarkdownContainer"] {
    display: none !important;
}
[data-testid="stPopover"] button[kind="tertiary"] > div > div[aria-hidden="true"] {
    display: none !important;
}
</style>"""
    st.markdown(css, unsafe_allow_html=True)


def init_session_state():
    if "unsaved_inputs" not in st.session_state:
        st.session_state["unsaved_inputs"] = {}
    if "active_input_id" not in st.session_state:
        st.session_state["active_input_id"] = BUILTIN_INPUT_ID
    if "studio_textarea" not in st.session_state:
        st.session_state["studio_textarea"] = ""
    if "promos_page_num" not in st.session_state:
        st.session_state["promos_page_num"] = 1
    if "promos_filter_sig" not in st.session_state:
        st.session_state["promos_filter_sig"] = None
    if "session_api_keys" not in st.session_state:
        st.session_state["session_api_keys"] = {}


@st.cache_data
def get_builtin_bundle() -> Dict[str, Any]:
    return load_builtin_bundle(DATA_FOLDER, OUTPUT_DIR)


def _empty_bundle() -> Dict[str, Any]:
    return {
        "id": "__empty__",
        "title": "No Active Project",
        "is_builtin": False,
        "is_saved": True,
        "is_empty": True,
        "created_at": "",
        "detection_mode": "manual",
        "detection_label": "Empty Workspace",
        "episode_count": 0,
        "promo_count": 0,
        "promos": [],
        "stitched_promos": [],
        "audit_report": {},
        "episodes": [],
        "telemetry": {},
    }


def resolve_active_bundle() -> Dict[str, Any]:
    active_id = st.session_state.get("active_input_id", BUILTIN_INPUT_ID)
    builtin_hidden = is_builtin_hidden()

    if active_id == BUILTIN_INPUT_ID and not builtin_hidden:
        return get_builtin_bundle()
    if active_id in st.session_state["unsaved_inputs"]:
        return st.session_state["unsaved_inputs"][active_id]
    if active_id not in (BUILTIN_INPUT_ID, "__empty__"):
        saved = load_saved_bundle(active_id)
        if saved is not None:
            return saved

    # Pick first available saved or draft project before empty state
    saved_list = list_saved_inputs()
    if saved_list:
        first_saved = load_saved_bundle(saved_list[0]["id"])
        if first_saved is not None:
            st.session_state["active_input_id"] = first_saved["id"]
            return first_saved
    if st.session_state["unsaved_inputs"]:
        first_uid = next(iter(st.session_state["unsaved_inputs"]))
        st.session_state["active_input_id"] = first_uid
        return st.session_state["unsaved_inputs"][first_uid]
    if not builtin_hidden:
        st.session_state["active_input_id"] = BUILTIN_INPUT_ID
        return get_builtin_bundle()

    st.session_state["active_input_id"] = "__empty__"
    return _empty_bundle()


def get_all_inputs_index() -> List[Dict[str, Any]]:
    """Returns a clean unified list of Built-in + Saved + Unsaved inputs."""
    items: List[Dict[str, Any]] = []
    if not is_builtin_hidden():
        builtin = get_builtin_bundle()
        items.append(
            {
                "id": BUILTIN_INPUT_ID,
                "title": builtin["title"],
                "status": "Built-in",
                "episode_count": builtin.get("episode_count", 50),
                "promo_count": builtin.get("promo_count", 0),
                "detection_label": builtin.get("detection_label", "Precomputed Benchmark"),
                "created_at": builtin.get("created_at", "Built-in Benchmark"),
                "switcher_label": f"Benchmark · {builtin['title']} ({builtin.get('promo_count', 0)})",
            }
        )

    for m in list_saved_inputs():
        items.append(
            {
                "id": m["id"],
                "title": m["title"],
                "status": "Saved",
                "episode_count": m.get("episode_count", 1),
                "promo_count": m.get("promo_count", 0),
                "detection_label": m.get("detection_label", ""),
                "created_at": m.get("created_at", ""),
                "switcher_label": f"Saved · {m['title']} ({m.get('promo_count', 0)})",
            }
        )

    for uid, ub in st.session_state["unsaved_inputs"].items():
        items.append(
            {
                "id": uid,
                "title": ub["title"],
                "status": "Unsaved",
                "episode_count": ub.get("episode_count", 1),
                "promo_count": len(ub.get("promos", [])),
                "detection_label": ub.get("detection_label", ""),
                "created_at": ub.get("created_at", "This session"),
                "switcher_label": f"Draft · {ub['title']} ({len(ub.get('promos', []))})",
            }
        )

    return items


def render_sidebar(active_bundle: Dict[str, Any]):
    st.sidebar.markdown("### Kuku Promo Studio")
    st.sidebar.caption("Vertical microdrama ad clip finder")

    all_items = get_all_inputs_index()
    ids = [item["id"] for item in all_items] or ["__empty__"]
    labels = {item["id"]: item["switcher_label"] for item in all_items}
    labels.setdefault("__empty__", "No projects available")
    current_id = active_bundle["id"] if active_bundle["id"] in ids else ids[0]

    st.session_state["sb_switcher_id"] = current_id

    def _on_switcher_change():
        st.session_state["active_input_id"] = st.session_state["sb_switcher_id"]
        st.session_state["promos_page_num"] = 1

    st.sidebar.selectbox(
        "Active project",
        options=ids,
        format_func=lambda x: labels.get(x, x),
        key="sb_switcher_id",
        on_change=_on_switcher_change,
        **select_kw(),
    )

    if st.sidebar.button("Home Explorer", icon=":material/home:", key="sb_go_home", **stretch_kw(st.button)):
        navigate_to("home")

    c1, c2 = st.sidebar.columns(2)
    with c1:
        if st.button("New Project", icon=":material/add:", key="sb_go_new", **stretch_kw(st.button)):
            navigate_to("new_input")
    with c2:
        if st.button("Projects", icon=":material/folder_open:", key="sb_go_lib", **stretch_kw(st.button)):
            navigate_to("library")

    st.sidebar.divider()
    with st.sidebar.expander("Export Active Promos", expanded=False):
        artifacts = build_export_artifacts(active_bundle)
        slug = active_bundle["id"]
        export_options = [
            ("txt", "Promo Cut Sheets (.txt)", f"{slug}_promos.txt", "text/plain", artifacts["txt"]),
            ("txt_zip", "Individual Promo .txt Files (.zip)", f"{slug}_promos_txt.zip", "application/zip", build_promos_txt_zip(active_bundle)),
            ("csv", "Ranked CSV (.csv)", f"{slug}_ranked.csv", "text/csv", artifacts["csv"]),
            ("json", "Master JSON (.json)", f"{slug}_promos.json", "application/json", artifacts["json"]),
            ("ffmpeg", "FFmpeg Script (.sh)", f"{slug}_cut_promos.sh", "text/plain", artifacts["ffmpeg"]),
            ("ffmpeg_bat", "FFmpeg Batch (.bat)", f"{slug}_cut_promos.bat", "text/plain", artifacts["ffmpeg_bat"]),
            ("edl", "Premiere / Resolve Markers (.csv)", f"{slug}_markers.csv", "text/csv", artifacts["edl"]),
        ]
        if os.path.exists("Solution_Document.pdf"):
            with open("Solution_Document.pdf", "rb") as f:
                pdf_bytes = f.read()
            export_options.append(
                ("pdf", "Solution Document (.pdf)", "Solution_Document.pdf", "application/pdf", pdf_bytes)
            )

        option_map = {opt[0]: opt for opt in export_options}
        chosen_fmt = st.selectbox(
            "Export format",
            options=[opt[0] for opt in export_options],
            format_func=lambda k: option_map[k][1],
            key="sb_export_fmt",
            **select_kw(),
        )
        _, _, fname, mime, payload = option_map[chosen_fmt]
        st.download_button(
            "Download File",
            data=payload,
            file_name=fname,
            mime=mime,
            icon=":material/download:",
            key=f"sb_dl_{chosen_fmt}",
            **stretch_kw(st.download_button),
        )


def render_active_header(active_bundle: Dict[str, Any], show_new_btn: bool = False, allow_switch: bool = False):
    if active_bundle.get("is_builtin"):
        pill_cls, pill_txt = "pill-builtin", "Built-in"
    elif active_bundle.get("is_saved"):
        pill_cls, pill_txt = "pill-saved", "Saved"
    else:
        pill_cls, pill_txt = "pill-temp", "Session Draft"

    mode_txt = active_bundle.get("detection_label", "Rule-Based")
    ep_cnt = int(active_bundle.get("episode_count", 0))
    pr_cnt = len(active_bundle.get("promos", []))
    created_txt = active_bundle.get("created_at", "")
    ep_lbl = "episode" if ep_cnt == 1 else "episodes"
    pr_lbl = "promo" if pr_cnt == 1 else "promos"

    all_items = get_all_inputs_index() if allow_switch else []
    if allow_switch and all_items:
        ids = [item["id"] for item in all_items]
        labels = {item["id"]: item["switcher_label"] for item in all_items}
        current_id = active_bundle["id"] if active_bundle["id"] in ids else ids[0]

        with st.container(border=True):
            sw_l, sw_r = st.columns([2.2, 2.8], vertical_alignment="center")
            with sw_l:
                def _on_inline_switch():
                    picked = st.session_state.get("hdr_project_pick")
                    if picked and picked != st.session_state.get("active_input_id"):
                        st.session_state["active_input_id"] = picked

                st.session_state["hdr_project_pick"] = current_id
                st.selectbox(
                    "Active project (per-project view)",
                    options=ids,
                    format_func=lambda x: labels.get(x, x),
                    key="hdr_project_pick",
                    on_change=_on_inline_switch,
                    **select_kw(),
                )
            with sw_r:
                info_html = "".join(
                    [
                        '<div style="display:flex;flex-direction:column;align-items:flex-end;gap:4px;padding-top:12px;">',
                        '<div class="context-title-row" style="justify-content:flex-end;">',
                        f'<span class="pill {pill_cls}">{clean_html(pill_txt)}</span>',
                        f'<span class="pill pill-mode">{clean_html(mode_txt)}</span>',
                        "</div>",
                        f'<div class="context-meta">{ep_cnt} {ep_lbl} · {pr_cnt} {pr_lbl} · {clean_html(created_txt)}</div>',
                        "</div>",
                    ]
                )
                st.markdown(info_html, unsafe_allow_html=True)

        if active_bundle.get("is_empty"):
            st.info("No active project right now. Add a new project or restore the built-in benchmark from Project Library.")
            return
    elif active_bundle.get("is_empty"):
        st.info("No active project right now. Add a new project or restore the built-in benchmark from Project Library.")
        return
    else:
        header_html = "".join(
            [
                '<div class="context-bar">',
                '<div class="context-title-row">',
                f'<span class="context-title">{clean_html(active_bundle["title"])}</span>',
                f'<span class="pill {pill_cls}">{clean_html(pill_txt)}</span>',
                f'<span class="pill pill-mode">{clean_html(mode_txt)}</span>',
                "</div>",
                f'<div class="context-meta">{ep_cnt} {ep_lbl} · {pr_cnt} {pr_lbl} · {clean_html(created_txt)}</div>',
                "</div>",
            ]
        )
        st.markdown(header_html, unsafe_allow_html=True)

    # Save / Discard bar for unsaved uploads
    if not active_bundle.get("is_saved") and not active_bundle.get("is_builtin"):
        with st.container(border=True):
            ub1, ub2, ub3 = st.columns([3.2, 1.1, 0.9])
            with ub1:
                edited_title = st.text_input(
                    "Unsaved session draft — edit title to save to Project Library",
                    value=active_bundle["title"],
                    key=f"hdr_rename_{active_bundle['id']}",
                )
            with ub2:
                st.markdown("<div style='height: 26px;'></div>", unsafe_allow_html=True)
                if st.button(
                    "Save Project",
                    type="primary",
                    key=f"hdr_save_{active_bundle['id']}",
                    **stretch_kw(st.button),
                ):
                    active_bundle["title"] = edited_title.strip() or active_bundle["title"]
                    saved_b = save_bundle_to_disk(active_bundle)
                    st.session_state["unsaved_inputs"].pop(active_bundle["id"], None)
                    st.session_state["active_input_id"] = saved_b["id"]
                    st.rerun()
            with ub3:
                st.markdown("<div style='height: 26px;'></div>", unsafe_allow_html=True)
                if st.button(
                    "Discard",
                    key=f"hdr_disc_{active_bundle['id']}",
                    **stretch_kw(st.button),
                ):
                    st.session_state["unsaved_inputs"].pop(active_bundle["id"], None)
                    st.session_state.pop("active_input_id", None)
                    st.rerun()


def render_promo_card(p: Dict[str, Any], key_prefix: str = "card", show_title: str = ""):
    segments = p.get("segments") or [{}]
    seg = segments[0]
    is_intercut = len(segments) > 1
    tier_full = str(p.get("marketing_tier", "Tier 1"))
    tier_short = tier_full.split(":")[0].strip()
    if "Tier 1" in tier_short:
        tier_cls = "badge-tier-1"
        card_tier_cls = "promo-card-t1"
    elif "Tier 2" in tier_short:
        tier_cls = "badge-tier-2"
        card_tier_cls = "promo-card-t2"
    else:
        tier_cls = "badge-tier-3"
        card_tier_cls = "promo-card-t3"

    method_txt = clean_html(p.get("detection_method", "Rule-Based"))
    judge_v = p.get("judge_verdict") or {}

    cut_badge_html = (
        f'<span class="promo-badge badge-judge">Intercut ({len(segments)} segs)</span>'
        if is_intercut
        else ""
    )
    judge_badge_html = (
        f'<span class="promo-badge badge-judge">Judge: {clean_html(judge_v.get("judge_score", p.get("total_score")))}/100</span>'
        if judge_v
        else ""
    )
    judge_box_html = (
        f'<div class="promo-judge"><b>Judge ({clean_html(judge_v.get("judge_provider", "LLM"))}):</b> {clean_html(judge_v.get("verdict", ""))}</div>'
        if judge_v and judge_v.get("verdict")
        else ""
    )

    start_ts = clean_html(seg.get("start_time", "00:00"))
    end_ts = clean_html(seg.get("end_time", "00:00"))
    dur_val = clean_html(p.get("total_duration_seconds", 0))

    card_html = "".join(
        [
            f'<div class="promo-card {card_tier_cls}">',
            '<div class="promo-header">',
            "<div>",
            f'<span class="promo-title">Rank #{clean_html(p.get("rank", "?"))} · Episode {clean_html(p.get("episode", 1))}</span>',
            f'<span class="promo-time">{start_ts} → {end_ts} ({dur_val}s)</span>',
            "</div>",
            '<div class="promo-badges">',
            cut_badge_html,
            f'<span class="promo-badge badge-method">{method_txt}</span>',
            f'<span class="promo-badge {tier_cls}">{clean_html(tier_short)}</span>',
            f'<span class="promo-badge badge-score">Score {clean_html(p.get("total_score", 0))}/100</span>',
            judge_badge_html,
            "</div>",
            "</div>",
            f'<div class="promo-row"><span class="tag-hook">0–3s Hook</span>{clean_html(p.get("hook", ""))}</div>',
            f'<div class="promo-row"><span class="tag-cliff">Cliffhanger</span>{clean_html(p.get("cliffhanger", ""))}</div>',
            f'<div class="promo-why"><b>Why it works:</b> {clean_html(p.get("why_it_works", ""))}</div>',
            judge_box_html,
            "</div>",
        ]
    )
    st.markdown(card_html, unsafe_allow_html=True)

    with st.expander(f"Script excerpt & breakdown · Rank #{p.get('rank', '?')} ({start_ts}–{end_ts})"):
        # Structured human-readable score breakdown + single-promo .txt download
        sc_cols = st.columns([1, 1, 1, 1, 1.3], vertical_alignment="center")
        sc_cols[0].caption(f"**Hook:** {p.get('hook_score', '—')}/10")
        sc_cols[1].caption(f"**Cliffhanger:** {p.get('cliffhanger_score', '—')}/10")
        sc_cols[2].caption(f"**Coherence:** {p.get('coherence_score', '—')}/10")
        sc_cols[3].caption(f"**Cut:** {'Intercut' if is_intercut else 'Single Cut'}")
        with sc_cols[4]:
            dl_key = f"dl_txt_{key_prefix}_{p.get('rank', 0)}_{p.get('episode', 1)}_{start_ts}_{end_ts}"
            st.download_button(
                "Download .txt",
                data=format_single_promo_txt(p, show_title=show_title),
                file_name=f"promo_rank{int(p.get('rank', 0)):02d}_ep{int(p.get('episode', 1)):02d}.txt",
                mime="text/plain",
                icon=":material/download:",
                key=dl_key,
                **stretch_kw(st.download_button),
            )

        if p.get("proposed_by"):
            st.caption(f"Detected by: {', '.join(p['proposed_by'])}")

        model_scores = p.get("model_scores") or {}
        if model_scores:
            rows = []
            for m_name, vals in model_scores.items():
                if isinstance(vals, dict):
                    rows.append(
                        {
                            "Model": m_name,
                            "Hook": vals.get("hook_score", "—"),
                            "Cliffhanger": vals.get("cliffhanger_score", "—"),
                            "Coherence": vals.get("coherence_score", "—"),
                            "Total": vals.get("total_score", "—"),
                        }
                    )
            if rows:
                st.dataframe(pd.DataFrame(rows), hide_index=True, **stretch_kw(st.dataframe))

        excerpts = p.get("script_excerpt", [])
        if excerpts:
            st.markdown("---")
            for b in excerpts:
                ts_txt = f"[{b.get('start')}–{b.get('end')}]"
                if b.get("type") == "DIALOGUE":
                    tone_txt = f" ({b.get('tone')})" if b.get("tone") else ""
                    st.markdown(
                        f"`{ts_txt}` **{b.get('speaker')}**{tone_txt}: \"{b.get('content')}\""
                    )
                else:
                    st.markdown(
                        f"`{ts_txt}` *[{b.get('type')}]* {b.get('content')}"
                    )
        else:
            st.caption("Script excerpt not available for this entry.")


def render_ai_provider_controls(
    key_prefix: str = "ai",
    default_single_judge: bool = True,
):
    """
    Renders Gemini / OpenAI provider selection, optional session-only keys,
    Multi-LLM strategy, and LLM-as-a-Judge controls cleanly without duplication.
    Returns (llm_providers, use_judge, judge_provider_name, run_all_active_llms).
    """
    statuses = get_backend_provider_status()
    ready_statuses = [s for s in statuses if s["configured"]]
    session_keys = st.session_state.get("session_api_keys", {})

    llm_providers: List[LLMProviderConfig] = []
    use_judge = False
    judge_provider_name = "auto"
    run_all_active_llms = True

    if ready_statuses:
        st.caption(
            "Server-configured providers are ready with default models. Automatic failover handles outages or rate limits."
        )
        chk_cols = st.columns(len(ready_statuses))
        for idx, st_item in enumerate(ready_statuses):
            p_name = st_item["name"]
            with chk_cols[idx]:
                use_this = st.checkbox(
                    f"{st_item['display_name']} (Ready)",
                    value=True,
                    key=f"{key_prefix}_srv_use_{p_name}",
                )
            if use_this and st_item["config"]:
                base_cfg = st_item["config"]
                llm_providers.append(
                    LLMProviderConfig(
                        name=p_name,
                        api_key=base_cfg.api_key,
                        model=base_cfg.model,
                        base_url=base_cfg.base_url,
                        enabled=True,
                    )
                )
    else:
        st.info(
            "No API keys configured in `.env` or `.streamlit/secrets.toml`. "
            "Paste a Gemini or OpenAI key below for this session."
        )

    show_session_keys = True if not ready_statuses else st.checkbox(
        "Add or override API keys for this session",
        value=False,
        key=f"{key_prefix}_show_sess_keys",
    )
    if show_session_keys:
        sk1, sk2 = st.columns(2)
        with sk1:
            gem_key = st.text_input(
                "Google Gemini API Key (optional)",
                value=session_keys.get("gemini", ""),
                type="password",
                placeholder="AIza...",
                key=f"{key_prefix}_sess_gemini",
            )
        with sk2:
            oai_key = st.text_input(
                "OpenAI API Key (optional)",
                value=session_keys.get("openai", ""),
                type="password",
                placeholder="sk-...",
                key=f"{key_prefix}_sess_openai",
            )
        st.caption(
            "Session-only (never saved to disk). Keys from Google AI Studio (aistudio.google.com/apikey) or OpenAI (platform.openai.com/api-keys)."
        )
        for p_name, p_key in (("gemini", gem_key), ("openai", oai_key)):
            cleaned = p_key.strip()
            if cleaned:
                st.session_state["session_api_keys"][p_name] = cleaned
                llm_providers = [p for p in llm_providers if p.name != p_name]
                llm_providers.append(
                    LLMProviderConfig(
                        name=p_name,
                        api_key=cleaned,
                        model=PROVIDER_DEFAULTS[p_name]["default_model"],
                        enabled=True,
                    )
                )

    if len(llm_providers) >= 2:
        j1, j2, j3 = st.columns([1.5, 1.3, 1.2])
        with j1:
            multi_strat = st.selectbox(
                "Multi-LLM strategy",
                ["Run both + Failover", "Failover chain only"],
                key=f"{key_prefix}_multi_strat",
                **select_kw(),
            )
            run_all_active_llms = multi_strat.startswith("Run both")
        with j2:
            st.markdown("<div style='height: 26px;'></div>", unsafe_allow_html=True)
            use_judge = st.checkbox(
                "Enable LLM-as-a-Judge",
                value=True,
                key=f"{key_prefix}_use_judge",
            )
        with j3:
            if use_judge:
                judge_opts = ["auto"] + [p.name for p in llm_providers]
                judge_labels = {"auto": "Auto (First Healthy)"}
                for p in llm_providers:
                    judge_labels[p.name] = p.display_name
                judge_provider_name = st.selectbox(
                    "Judge provider",
                    judge_opts,
                    format_func=lambda x: judge_labels.get(x, x),
                    key=f"{key_prefix}_judge_prov",
                    **select_kw(),
                )
    elif len(llm_providers) == 1:
        use_judge = st.checkbox(
            "Run LLM-as-a-Judge pass to score & rank candidates",
            value=default_single_judge,
            key=f"{key_prefix}_use_judge_single",
        )
        judge_provider_name = llm_providers[0].name

    return llm_providers, use_judge, judge_provider_name, run_all_active_llms
